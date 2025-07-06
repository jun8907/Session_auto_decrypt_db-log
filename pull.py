import subprocess
import os

def su_pull(remote_path, local_path):
    temp_path = f"/sdcard/{os.path.basename(local_path)}"

    try:
        print(f"[*] su 권한으로 {remote_path} → {temp_path} 복사 중...")
        subprocess.run(["adb", "shell", f"su -c 'cp {remote_path} {temp_path}'"], shell=True, check=True)

        print(f"[*] {temp_path} → {local_path} 로컬로 추출 중...")
        subprocess.run(["adb", "pull", temp_path, local_path], check=True)

        print(f"[+] 추출 완료: {local_path}")
    except subprocess.CalledProcessError as e:
        print(f"[!] 오류 발생 ({remote_path}): {e}")

def pull_all_artifacts():
    os.makedirs("extracted_files", exist_ok=True)
    os.makedirs("log_files", exist_ok=True)

    package = "network.loki.messenger"

    # 1. preferences 설정 파일
    su_pull(f"/data/data/{package}/shared_prefs/{package}_preferences.xml",
            os.path.join("extracted_files", f"{package}_preferences.xml"))
    
    # 2. 키스토어 파일
    su_pull("/data/misc/keystore/persistent.sqlite",
            os.path.join("extracted_files", "persistent.sqlite"))

    # ✅ 3. session.db 추가 추출
    su_pull(f"/data/data/{package}/databases/session.db",
            os.path.join("extracted_files", "session.db"))

    # 4. 로그 디렉터리 내부 파일 전부 추출
    print("[*] 로그 파일 목록 가져오는 중...")
    result = subprocess.run(
        ["adb", "shell", f"su -c 'ls /data/data/{package}/cache/log/'"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    filenames = result.stdout.strip().split('\n')
    if not filenames or filenames == ['']:
        print("[!] 로그 디렉터리에 파일이 없거나 접근 실패")
        return

    for filename in filenames:
        remote_log_path = f"/data/data/{package}/cache/log/{filename}"
        local_log_path = os.path.join("log_files", filename)
        su_pull(remote_log_path, local_log_path)

if __name__ == "__main__":
    pull_all_artifacts()
