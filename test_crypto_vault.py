# -*- coding: utf-8 -*-
"""
UNIT TEST SUITE FOR CRYPTO VAULT & DATA PROTECTION GATE
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from crypto_vault import (
    encrypt_value,
    decrypt_value,
    is_authorized_manager,
    mask_sensitive_dict,
    CryptoVaultManager,
    ENVELOPE_PREFIX
)

def run_tests():
    print("==================================================================")
    print("  RUNNING PYTHON CRYPTO VAULT TEST SUITE (quan-ly-tien-phong)     ")
    print("==================================================================")
    
    passphrase = "MasterKeySecret#2026!Admin"
    secret_text = "SECRET_TELEGRAM_TOKEN_987654321_XYZZ"

    # 1. Encrypt and decrypt roundtrip
    envelope = encrypt_value(secret_text, passphrase)
    assert envelope.startswith(ENVELOPE_PREFIX), "Phải bắt đầu bằng ENVELOPE_PREFIX"
    decrypted = decrypt_value(envelope, passphrase)
    assert decrypted == secret_text, f"Giải mã sai: {decrypted} != {secret_text}"
    print("  ✓ 1. Mã hóa & Giải mã AES-256-GCM thành công tuyệt đối")

    # 2. Tampered or wrong key
    try:
        decrypt_value(envelope, "WrongPassword123")
        assert False, "Phải ném ngoại lệ khi dùng sai mật khẩu"
    except Exception:
        print("  ✓ 2. Chặn giải mã khi sai Master Key an toàn")

    # 3. Manager authorization
    assert is_authorized_manager("mrkun28@gmail.com") == True
    assert is_authorized_manager("MRKUN28@GMAIL.COM") == True
    assert is_authorized_manager("anaa2700") == True
    assert is_authorized_manager("stranger@hacker.com") == False
    assert is_authorized_manager("") == False
    print("  ✓ 3. Xác thực quyền quản lý mrkun28@gmail.com chuẩn xác")

    # 4. Sensitive Data Masking for non-managers
    raw_config = {
        "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "api_key": "live_secret_key_111",
        "public_url": "https://ananasux.github.io/Website_thoitiet_design/",
        "system_status": "ONLINE"
    }

    masked = mask_sensitive_dict(raw_config, is_manager=False)
    assert "******" in masked["bot_token"]
    assert "******" in masked["api_key"]
    assert masked["public_url"] == "https://ananasux.github.io/Website_thoitiet_design/"
    assert masked["system_status"] == "ONLINE"
    print("  ✓ 4. Tự động che giấu (mask) dữ liệu nhạy cảm cho người dùng ngoài")

    # 5. Full data for manager
    manager_view = mask_sensitive_dict(raw_config, is_manager=True)
    assert manager_view["bot_token"] == raw_config["bot_token"]
    assert manager_view["api_key"] == raw_config["api_key"]
    print("  ✓ 5. Người quản lý mrkun28@gmail.com đọc được 100% dữ liệu gốc")

    # 6. CryptoVaultManager integration
    vault = CryptoVaultManager()
    assert vault.is_unlocked() == False
    vault.unlock(passphrase)
    assert vault.is_unlocked() == True
    recovered = vault.secure_get("TEST_SECRET_VAR", encrypted_default=envelope)
    assert recovered == secret_text
    vault.lock()
    assert vault.is_unlocked() == False
    print("  ✓ 6. CryptoVaultManager quản lý phiên mở khóa in-memory an toàn")

    print("==================================================================")
    print("  KẾT QUẢ: TOÀN BỘ 6/6 PHÉP THỬ CRYPTO VAULT PYTHON ĐẠT 100% PASS ")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
