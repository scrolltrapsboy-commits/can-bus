"""Notebook-derived CAN simulation, feature engineering and IsolationForest run."""
import math, random, threading, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import can, joblib
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

OUT=Path(__file__).resolve().parent.parent/"outputs"; OUT.mkdir(exist_ok=True)
DURATION=300; WINDOW=5; SEED=42
CHANNELS=[(0x100,"Electronic_Channel_A",.010),(0x101,"Electronic_Channel_B",.020),(0x102,"Electronic_Channel_C",.050),(0x103,"Electronic_Channel_D",.100)]
IDS=[x[0] for x in CHANNELS]; VALID=[hex(x) for x in IDS]
FEATURES=["message_count","unique_can_ids","can_id_0x100_frequency","can_id_0x101_frequency","can_id_0x102_frequency","can_id_0x103_frequency","mean_inter_arrival","std_inter_arrival","max_inter_arrival","payload_mean","payload_std","payload_min","payload_max","payload_range","extreme_byte_count"]
lock=threading.Lock()
state={"status":"idle","progress":0,"stage":"Ready — press Start Pipeline","error":None,"summary":None,"telemetry":[],"results":[],"logs":[]}
def snapshot():
 with lock: return dict(state)
def setstate(**kw):
 with lock: state.update(kw)
def log(s):
 with lock:
  state["logs"].append({"time":datetime.now(timezone.utc).strftime("%H:%M:%S"),"message":str(s)})
  state["logs"]=state["logs"][-120:]
def scenario(t): return "NORMAL" if t<100 else ("EARLY_DEGRADATION" if t<200 else "SEVERE_ABNORMALITY")
def payload(ci,t,sc):
 base=[60,110,150,200][ci]; noise=random.gauss(0,2); wave=8*math.sin(t/5+ci)
 if sc=="NORMAL": deg,extra=0,0
 elif sc=="EARLY_DEGRADATION": deg,extra=(t-100)*.35,random.gauss(0,4)
 else: deg,extra=(t-200)*.9,random.gauss(0,10)
 p=[int(np.clip(base+wave+noise+deg+extra+random.gauss(0,1),0,255)) for _ in range(8)]
 if sc=="EARLY_DEGRADATION": p[0]=int(np.clip(p[0]+random.gauss(0,8),0,255))
 elif sc=="SEVERE_ABNORMALITY":
  p[0]=int(np.clip(p[0]+random.gauss(0,25),0,255)); p[4]=int(np.clip(p[4]+random.gauss(0,25),0,255))
  if random.random()<.12: p[7]=random.choice([0,255])
 return bytes(p)
def run_pipeline():
 if snapshot()["status"]=="running": return
 setstate(status="running",progress=1,stage="Initializing notebook pipeline",error=None,summary=None,telemetry=[],results=[],logs=[])
 try:
  random.seed(SEED); np.random.seed(SEED)
  log("PROJECT 18 — Predictive Failure Detection in Automotive Systems")
  log(f"Using notebook pipeline: python-can {can.__version__}, pandas {pd.__version__}, NumPy {np.__version__}")
  setstate(progress=5,stage="Simulating virtual CAN bus — 300 virtual seconds")
  bus=can.Bus(interface="virtual",channel="project18_can_bus_web",receive_own_messages=False)
  rows=[]; t=0.0
  while t<DURATION:
   cid,name,period=random.choice(CHANNELS); variation=.03 if t<100 else (.10 if t<200 else .25)
   t+=max(period+random.gauss(0,period*variation),.001)
   if t>=DURATION: break
   sc=scenario(t); p=payload(IDS.index(cid),t,sc)
   bus.send(can.Message(arbitration_id=cid,data=p,is_extended_id=False))
   rows.append({"timestamp":round(t,6),"can_id":hex(cid),"channel":name,"payload_hex":p.hex(),"scenario":sc})
  bus.shutdown(); raw=pd.DataFrame(rows); raw.to_csv(OUT/"can_telemetry_raw.csv",index=False)
  log(f"CAN simulation complete: {len(raw):,} frames; scenarios {raw.scenario.value_counts().to_dict()}")
  setstate(progress=24,stage="Preprocessing and validating payloads")
  df=raw.drop_duplicates().copy(); df["timestamp"]=pd.to_numeric(df.timestamp,errors="coerce")
  df["can_id"]=df.can_id.astype(str).str.lower().str.strip(); df["payload_hex"]=df.payload_hex.astype(str).str.lower().str.strip()
  df=df.dropna(subset=["timestamp","can_id","payload_hex","scenario"]); df=df[df.can_id.isin(VALID)&(df.payload_hex.str.len()==16)].copy()
  def validhex(x):
   try: bytes.fromhex(x); return True
   except ValueError: return False
  df=df[df.payload_hex.apply(validhex)].sort_values("timestamp").reset_index(drop=True)
  for i in range(8): df[f"payload_byte_{i}"]=df.payload_hex.apply(lambda x,i=i:int(x[i*2:i*2+2],16))
  df["inter_arrival_time"]=df.groupby("can_id").timestamp.diff(); df["inter_arrival_time"]=df.inter_arrival_time.fillna(df.inter_arrival_time.median())
  df.to_csv(OUT/"can_telemetry_preprocessed.csv",index=False)
  setstate(progress=40,stage="Engineering notebook 5-second time-window features")
  df["window_id"]=(df.timestamp//WINDOW).astype(int); rows=[]
  pb=[f"payload_byte_{i}" for i in range(8)]
  for wid,w in df.groupby("window_id"):
   r={"window_id":int(wid),"window_start":float(wid*WINDOW),"scenario":w.scenario.mode().iloc[0],"message_count":len(w),"unique_can_ids":w.can_id.nunique()}
   for cid in VALID: r[f"can_id_{cid}_frequency"]=int(w.can_id.eq(cid).sum())
   iat=w.inter_arrival_time; r.update(mean_inter_arrival=float(iat.mean()),std_inter_arrival=float(iat.std() or 0),max_inter_arrival=float(iat.max()))
   v=w[pb].values.flatten(); r.update(payload_mean=float(np.mean(v)),payload_std=float(np.std(v)),payload_min=int(np.min(v)),payload_max=int(np.max(v)),payload_range=int(np.max(v)-np.min(v)),extreme_byte_count=int(np.sum((v==0)|(v==255))))
   rows.append(r)
  feat=pd.DataFrame(rows).fillna(0); feat.to_csv(OUT/"can_window_features.csv",index=False)
  log(f"Feature table created: {len(feat)} windows, {len(FEATURES)} ML features")
  setstate(progress=58,stage="Training Isolation Forest on NORMAL windows only")
  xnormal=feat.loc[feat.scenario=="NORMAL",FEATURES]; model=IsolationForest(n_estimators=300,contamination="auto",random_state=SEED,n_jobs=-1); model.fit(xnormal)
  feat["anomaly_score"]=-model.decision_function(feat[FEATURES]); scores=feat.loc[feat.scenario=="NORMAL","anomaly_score"]
  wt=float(scores.quantile(.95)); ct=float(scores.quantile(.99))
  feat["alert_status"]=feat.anomaly_score.apply(lambda x:"CRITICAL" if x>=ct else ("WARNING" if x>=wt else "NORMAL"))
  mapping={"NORMAL":"NORMAL","EARLY_DEGRADATION":"WARNING","SEVERE_ABNORMALITY":"CRITICAL"}; feat["true_alert"]=feat.scenario.map(mapping)
  labels=["NORMAL","WARNING","CRITICAL"]; cm=confusion_matrix(feat.true_alert,feat.alert_status,labels=labels)
  precision=float(precision_score(feat.true_alert,feat.alert_status,labels=labels,average="weighted",zero_division=0)); recall=float(recall_score(feat.true_alert,feat.alert_status,labels=labels,average="weighted",zero_division=0)); f1=float(f1_score(feat.true_alert,feat.alert_status,labels=labels,average="weighted",zero_division=0))
  actual=feat.true_alert!="NORMAL"; pred=feat.alert_status!="NORMAL"; tn=int(np.sum((~actual)&(~pred))); fp=int(np.sum((~actual)&pred)); fn=int(np.sum(actual&(~pred))); tp=int(np.sum(actual&pred))
  fpr=fp/(fp+tn) if fp+tn else 0; fnr=fn/(fn+tp) if fn+tp else 0
  feat.to_csv(OUT/"project18_final_results.csv",index=False)
  joblib.dump({"model":model,"feature_columns":FEATURES,"warning_threshold":wt,"critical_threshold":ct,"random_state":SEED},OUT/"isolation_forest_model.joblib")
  log(f"Isolation Forest fit complete — 300 trees; warning={wt:.6f}; critical={ct:.6f}")
  log(f"Weighted metrics — precision {precision:.4f}, recall {recall:.4f}, F1 {f1:.4f}")
  log(f"Error rates — false positive {fpr:.4f}, false negative {fnr:.4f}")
  telemetry=[]
  for _,r in feat.tail(60).iterrows():
   telemetry.append({"time":float(r.window_start),"rpm":int(1200+min(r.payload_mean*12,2600)),"temp":round(65+min(r.payload_mean*.12,35),1),"voltage":round(14.2-min(r.extreme_byte_count*.025,1),2),"score":round(float(r.anomaly_score),6),"scenario":str(r.scenario),"alert":str(r.alert_status),"messages":int(r.message_count)})
  summary={"frames_generated":int(len(raw)),"preprocessed_frames":int(len(df)),"windows":int(len(feat)),"ml_features":len(FEATURES),"normal_training_windows":int(len(xnormal)),"warning_threshold":wt,"critical_threshold":ct,"precision":precision,"recall":recall,"f1":f1,"false_positive_rate":fpr,"false_negative_rate":fnr,"alerts":{str(k):int(v) for k,v in feat.alert_status.value_counts().to_dict().items()},"confusion_matrix":cm.tolist(),"labels":labels,"scenario_counts":{str(k):int(v) for k,v in raw.scenario.value_counts().to_dict().items()},"outputs":["can_telemetry_raw.csv","can_telemetry_preprocessed.csv","can_window_features.csv","project18_final_results.csv","isolation_forest_model.joblib"]}
  setstate(progress=100,stage="Notebook pipeline completed",status="completed",summary=summary,telemetry=telemetry,results=feat.tail(20).replace({np.nan:None}).to_dict(orient="records"))
  log("Pipeline complete. Values are the output of this run on notebook-generated simulated CAN data.")
 except Exception as e:
  log(f"PIPELINE ERROR: {type(e).__name__}: {e}"); setstate(status="error",stage="Pipeline failed",error=f"{type(e).__name__}: {e}")
