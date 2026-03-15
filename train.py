import os, re, sys, logging
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from scipy.sparse import hstack, csr_matrix

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("train_multi")

# =====================================================================
# AYARLAR: Eğitmek istediğin veri setini buradan seç! ("BGL" veya "HDFS")
# =====================================================================
DATASET_MODE = "HDFS"  
MAX_LINES = 'None' # 32 GB RAM şovu için None kalsın :)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "saved_models")

# Moduna göre dosya isimlerini dinamik belirliyoruz
if DATASET_MODE == "BGL":
    LOG_NAMES = ["BGL.log", "bgl2", "BGL_500k.log", "bgl.log"]
    OUT_CSV   = os.path.join(DATA_DIR, "bgl_train_ready.csv")
    MODEL_PREFIX = ""
else:
    LOG_NAMES = ["HDFS_1.log", "HDFS.log", "hdfs.log"]
    OUT_CSV   = os.path.join(DATA_DIR, "hdfs_train_ready.csv")
    MODEL_PREFIX = "hdfs_"

TARGET_PATH = None
for _name in LOG_NAMES:
    _p = os.path.join(DATA_DIR, _name)
    if os.path.exists(_p):
        TARGET_PATH = _p
        break

# =====================================================================
# 1. VERİ HAZIRLAMA (BGL ve HDFS için Çift Motor)
# =====================================================================
def prepare_data() -> pd.DataFrame:
    if TARGET_PATH is None:
        sys.exit(
            f"HATA: {DATASET_MODE} log dosyası bulunamadı!\n"
            f"Lütfen dosyayı şu konuma koy: {os.path.join(DATA_DIR, LOG_NAMES[0])}"
        )

    log.info("%s dosyası işleniyor: %s", DATASET_MODE, TARGET_PATH)
    log.info("Maksimum satır: %s", MAX_LINES or "Tümü")

    # Regex Kuralları
    bgl_re = re.compile(
        r"^(-|[A-Z0-9_]+)\s+\d+\s+\d{4}\.\d{2}\.\d{2}\s+\S+\s+\S+\s+(\S+)\s+\S+\s+(\S+)\s+(\w+)\s+(.+)$"
    )
    hdfs_re = re.compile(r"^\d{6}\s+\d{6}\s+\d+\s+(\w+)\s+[^\s:]+:\s+(.+)$")

    records = []
    skipped = 0
    total   = 0

    with open(TARGET_PATH, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            if MAX_LINES != 'None' and total >= int(MAX_LINES):
                break
            line = raw.strip()
            if not line:
                continue
            total += 1

            if DATASET_MODE == "BGL":
                m = bgl_re.match(line)
                if not m:
                    skipped += 1
                    continue
                flag, node2, component, level, message = m.groups()
                label = _map_label(flag)
                level = _norm_level(level)
                service = component
            else:
                # HDFS Okuma Mantığı
                m = hdfs_re.match(line)
                if not m:
                    skipped += 1
                    continue
                level, message = m.groups()
                level = _norm_level(level)
                # Basit bir Heuristic: Warn/Error/Fatal seviyelerini anomali kabul et
                label = "SystemFailure" if level in ["ERROR", "CRITICAL", "WARNING"] else "Normal"
                service = "HDFS_Node"

            records.append({
                "level":   level,
                "service": service,
                "message": message,
                "label":   label,
            })

            if len(records) % 500_000 == 0:
                log.info("  %d satır işlendi...", len(records))

    df = pd.DataFrame(records)

    log.info("Parse tamamlandı: %d kayıt, %d satır atlandı", len(df), skipped)
    log.info("Label dağılımı:\n%s", df["label"].value_counts().to_string())

    # Tekilleştirme Sınırları (HDFS'de Normal log çok tekrar ettiği için limit esnek)
    normal_limit = 1000 if DATASET_MODE == "HDFS" else 500
    CLASS_LIMITS = {"Normal": normal_limit, "SystemFailure": 5000, "AppError": 5000}
    
    parts = []
    for lbl, grp in df.groupby("label", sort=False):
        limit = CLASS_LIMITS.get(lbl, 50)
        parts.append(grp.groupby("message", sort=False).head(limit))
        
    df = (pd.concat(parts)
            .sample(frac=1, random_state=42)
            .reset_index(drop=True))
            
    log.info("Tekilleştirme sonrası: %d satır", len(df))
    
    anomaly_ratio = (df["label"] != "Normal").mean()
    if anomaly_ratio < 0.01:
        log.warning("Anomali oranı çok düşük (%.2f%%) — model zayıf kalabilir!", anomaly_ratio * 100)

    df.to_csv(OUT_CSV, index=False)
    log.info("CSV kaydedildi: %s", OUT_CSV)
    return df

def _map_label(flag: str) -> str:
    flag = flag.strip()
    if flag == "-": return "Normal"
    flag_up = flag.upper()
    if "FATAL" in flag_up or "KERN" in flag_up: return "SystemFailure"
    if "APP" in flag_up: return "AppError"
    if "HARDWARE" in flag_up or "HW" in flag_up: return "HardwareFailure"
    return "UnknownAnomaly"

def _norm_level(level: str) -> str:
    MAP = {"WARN": "WARNING", "FATAL": "CRITICAL", "ERR": "ERROR", "SEVERE": "CRITICAL"}
    return MAP.get(level.upper(), level.upper())

# =====================================================================
# 2. FEATURE EXTRACTION
# =====================================================================
def extract_features(df: pd.DataFrame):
    LEVEL_ORDER = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "UNKNOWN"]

    le = LabelEncoder().fit(LEVEL_ORDER)
    safe_levels = df["level"].apply(lambda x: x if x in LEVEL_ORDER else "UNKNOWN")
    level_enc = le.transform(safe_levels).reshape(-1, 1)

    tfidf = TfidfVectorizer(max_features=1000, sublinear_tf=True, ngram_range=(1, 2))
    tfidf_mat = tfidf.fit_transform(df["message"].fillna(""))

    time_delta = np.zeros((len(df), 1))

    X = hstack([csr_matrix(np.hstack([level_enc, time_delta])), tfidf_mat]).toarray()
    log.info("Feature matrix: %s", X.shape)
    return X, tfidf, le

# =====================================================================
# 3. MODEL EĞİTİMİ (Dinamik Kayıt İsimleri ile)
# =====================================================================
def train(df: pd.DataFrame, X: np.ndarray):
    os.makedirs(MODEL_DIR, exist_ok=True)

    anomaly_ratio = float((df["label"] != "Normal").mean())
    contamination = float(np.clip(anomaly_ratio, 0.01, 0.49))
    
    log.info("Isolation Forest eğitiliyor...")
    iso = IsolationForest(contamination=contamination, n_estimators=200, random_state=42, n_jobs=-1)
    iso.fit(X)
    
    iso_path = os.path.join(MODEL_DIR, f"{MODEL_PREFIX}iso_forest.joblib")
    joblib.dump(iso, iso_path)
    log.info("  ✅ %s kaydedildi.", os.path.basename(iso_path))

    y = df["label"].values
    counts = pd.Series(y).value_counts()
    rare   = counts[counts < 2].index.tolist()
    if rare:
        y = np.where(np.isin(y, rare), "UnknownAnomaly", y)

    use_stratify = pd.Series(y).value_counts().min() >= 2
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if use_stratify else None)

    log.info("Random Forest eğitiliyor... (bu biraz sürebilir)")
    rf = RandomForestClassifier(n_estimators=200, max_depth=15, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)

    y_pred = rf.predict(X_te)
    f1     = f1_score(y_te, y_pred, average="weighted")
    log.info("Test F1 (weighted): %.3f", f1)
    log.info("\n%s", classification_report(y_te, y_pred, zero_division=0))

    rf_path = os.path.join(MODEL_DIR, f"{MODEL_PREFIX}rf_classifier.joblib")
    joblib.dump(rf, rf_path)
    log.info("  ✅ %s kaydedildi.", os.path.basename(rf_path))

    return iso, rf

# =====================================================================
# 4. FEATURE EXTRACTOR KAYDET
# =====================================================================
def save_extractor(tfidf, le):
    sys.path.insert(0, BASE_DIR)
    ext_path = os.path.join(MODEL_DIR, f"{MODEL_PREFIX}feature_extractor.joblib")
    try:
        from utils.feature_extractor import FeatureExtractor
        ext = FeatureExtractor.__new__(FeatureExtractor)
        ext.tfidf              = tfidf
        ext.level_encoder      = le
        ext._is_fitted         = True
        ext.max_tfidf_features = 1000
        ext.feature_names      = (["level_encoded", "time_delta_sec"] + tfidf.get_feature_names_out().tolist())
        joblib.dump(ext, ext_path)
    except ImportError:
        obj = {"tfidf": tfidf, "level_encoder": le,
               "feature_names": (["level_encoded", "time_delta_sec"] + tfidf.get_feature_names_out().tolist())}
        joblib.dump(obj, ext_path)
    log.info("  ✅ %s kaydedildi.", os.path.basename(ext_path))

# =====================================================================
# MAIN
# =====================================================================
if __name__ == "__main__":
    log.info("=" * 55)
    log.info("LogNomaly — %s Eğitim Scripti", DATASET_MODE)
    log.info("=" * 55)

    df           = prepare_data()
    X, tfidf, le = extract_features(df)
    iso, rf      = train(df, X)
    save_extractor(tfidf, le)

    log.info("\n✅ Eğitim tamamlandı!")
    log.info("   Kaydedilen modeller: %s", MODEL_DIR)
    log.info("   Lütfen BGL ve HDFS modellerini app.py içinde dinamik çağırın.")