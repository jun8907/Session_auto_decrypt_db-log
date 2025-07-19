from preferences_log import extract_and_convert_data_iv as extract_log_iv
from preferences_database import extract_and_convert_data_iv as extract_db_iv
from persistent import extract_all_signalsecret_keys
from Crypto.Cipher import AES


def get_sqlcipher_key(xml_path, key_list, label):
    ciphertext, gcm_tag, iv = xml_path
    for idx, key in enumerate(key_list):
        print(f"\n[*] {label}용 SignalSecret #{idx+1} 복호화 시도 중...")
        try:
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            plaintext = cipher.decrypt_and_verify(ciphertext, gcm_tag)
            hex_key = plaintext.hex()
            print(f"[+] {label} 복호화 성공! SQLCipher Key (hex): {hex_key}")
            return hex_key
        except Exception:
            continue
    print(f"[!] {label} 복호화 실패")
    return None


def get_sqlcipher_keys():
    
    sqlite_path = "extracted_files/persistent.sqlite"
    key_list = extract_all_signalsecret_keys(sqlite_path)
    if not key_list:
        return None, None

    
    log_iv = extract_log_iv("extracted_files/network.loki.messenger_preferences.xml")
    db_iv = extract_db_iv("extracted_files/network.loki.messenger_preferences.xml")

    if not log_iv or not db_iv:
        print("[!] XML에서 IV 추출 실패")
        return None, None

    
    log_key = get_sqlcipher_key(log_iv, key_list, "로그 DB")
    db_key = get_sqlcipher_key(db_iv, key_list, "메시지 DB")

    return log_key, db_key



if __name__ == "__main__":
    log_key, db_key = get_sqlcipher_keys()
    print(f"\n[최종 결과] 로그 키: {log_key}")
    print(f"[최종 결과] DB 키: {db_key}")
