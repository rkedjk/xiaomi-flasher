#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Router 4A - Автоматический откат на стоковую прошивку
"""

import paramiko
from scp import SCPClient
import os
import sys
import time
import glob

class XiaomiFlasher:
    def __init__(self, router_ip, username, password, firmware_path):
        self.router_ip = router_ip
        self.username = username
        self.password = password
        self.firmware_path = firmware_path
        self.ssh_client = None
        
    def connect(self):
        """Подключение к роутеру по SSH"""
        try:
            print(f"[*] Подключение к {self.router_ip}...")
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                self.router_ip,
                username=self.username,
                password=self.password,
                timeout=15,
                look_for_keys=False,
                allow_agent=False
            )
            print("[+] Подключение установлено")
            return True
        except paramiko.AuthenticationException:
            print("[-] Ошибка аутентификации. Проверьте пароль.")
            return False
        except Exception as e:
            print(f"[-] Ошибка подключения: {e}")
            return False
    
    def upload_firmware(self):
        """Загрузка прошивки на роутер"""
        try:
            filesize = os.path.getsize(self.firmware_path) / (1024 * 1024)
            print(f"[*] Загрузка прошивки {os.path.basename(self.firmware_path)} ({filesize:.2f} MB)...")
            
            scp = SCPClient(self.ssh_client.get_transport(), progress=self.progress)
            scp.put(self.firmware_path, '/tmp/stock_firmware.bin')
            scp.close()
            
            print("\n[+] Прошивка загружена в /tmp/")
            return True
        except Exception as e:
            print(f"\n[-] Ошибка загрузки: {e}")
            return False
    
    def progress(self, filename, size, sent):
        """Прогресс загрузки файла"""
        percent = int((sent / size) * 100)
        bar = '=' * (percent // 2) + '>' + ' ' * (50 - percent // 2)
        print(f"\r[{bar}] {percent}%", end='', flush=True)
    
    def verify_mtd(self):
        """Проверка разделов MTD"""
        try:
            print("[*] Проверка разделов MTD...")
            stdin, stdout, stderr = self.ssh_client.exec_command("cat /proc/mtd")
            output = stdout.read().decode()
            
            if "OS1" in output or "firmware" in output:
                print("[+] Раздел для прошивки найден")
                return True
            else:
                print("[-] Раздел OS1/firmware не найден")
                print(output)
                return False
        except Exception as e:
            print(f"[-] Ошибка проверки MTD: {e}")
            return False
    
    def flash_firmware(self):
        """Прошивка стоковой прошивки"""
        try:
            print("\n" + "=" * 60)
            print("[*] НАЧАЛО ПРОШИВКИ")
            print("[!] НЕ ВЫКЛЮЧАЙТЕ РОУТЕР И НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ!")
            print("=" * 60 + "\n")
            
            # Выполняем команду прошивки
            stdin, stdout, stderr = self.ssh_client.exec_command(
                "mtd -r write /tmp/stock_firmware.bin OS1",
                get_pty=True
            )
            
            # Читаем вывод в реальном времени
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    output = stdout.channel.recv(1024).decode()
                    print(output, end='')
                time.sleep(0.5)
            
            print("\n" + "=" * 60)
            print("[+] Прошивка завершена, роутер перезагружается...")
            print("[*] Подождите 2-3 минуты до полной загрузки")
            print("[*] Роутер будет доступен по адресу 192.168.31.1")
            print("=" * 60)
            return True
        except Exception as e:
            # Это нормально, что соединение оборвется при перезагрузке
            if "closed" in str(e).lower() or "connection" in str(e).lower():
                print("\n" + "=" * 60)
                print("[+] Роутер перезагружается...")
                print("[*] Подождите 2-3 минуты до полной загрузки")
                print("[*] Роутер будет доступен по адресу 192.168.31.1")
                print("=" * 60)
                return True
            print(f"[-] Ошибка прошивки: {e}")
            return False
    
    def run(self):
        """Запуск полного процесса"""
        if not os.path.exists(self.firmware_path):
            print(f"[-] Файл прошивки не найден: {self.firmware_path}")
            return False
        
        if not self.connect():
            return False
        
        if not self.verify_mtd():
            self.ssh_client.close()
            return False
        
        if not self.upload_firmware():
            self.ssh_client.close()
            return False
        
        success = self.flash_firmware()
        
        try:
            self.ssh_client.close()
        except:
            pass
        
        return success

def find_firmware():
    """Автоматический поиск файла прошивки"""
    # Получаем директорию где находится исполняемый файл
    if getattr(sys, 'frozen', False):
        # Если запущен как EXE
        app_dir = os.path.dirname(sys.executable)
    else:
        # Если запущен как скрипт
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ищем .bin файлы в директории
    patterns = [
        os.path.join(app_dir, "*.bin"),
        os.path.join(app_dir, "miwifi*.bin"),
        os.path.join(app_dir, "stock*.bin"),
        os.path.join(app_dir, "firmware*.bin")
    ]
    
    firmware_files = []
    for pattern in patterns:
        firmware_files.extend(glob.glob(pattern))
    
    # Убираем дубликаты
    firmware_files = list(set(firmware_files))
    
    if len(firmware_files) == 0:
        return None
    elif len(firmware_files) == 1:
        return firmware_files[0]
    else:
        # Если несколько файлов - выбираем первый подходящий
        print("[*] Найдено несколько прошивок:")
        for i, fw in enumerate(firmware_files, 1):
            print(f"    {i}. {os.path.basename(fw)}")
        print(f"[*] Используется: {os.path.basename(firmware_files[0])}")
        return firmware_files[0]

def main():
    print("=" * 60)
    print("    Xiaomi Router 4A - Откат на стоковую прошивку")
    print("=" * 60)
    print()
    
    # Дефолтные параметры OpenWRT
    router_ip = "192.168.1.1"
    username = "root"
    password = ""
    
    print("[*] Используются дефолтные параметры OpenWRT:")
    print(f"    IP адрес: {router_ip}")
    print(f"    Логин: {username}")
    print(f"    Пароль: <пустой>")
    print()
    
    # Автопоиск прошивки
    print("[*] Поиск файла прошивки...")
    firmware_path = find_firmware()
    
    if not firmware_path:
        print("[-] Файл прошивки (.bin) не найден!")
        print("[!] Положите файл прошивки рядом с программой")
        print()
        input("Нажмите Enter для выхода...")
        return 1
    
    print(f"[+] Найдена прошивка: {os.path.basename(firmware_path)}")
    filesize = os.path.getsize(firmware_path) / (1024 * 1024)
    print(f"[+] Размер: {filesize:.2f} MB")
    print()
    
    # Подтверждение
    response = input("Начать прошивку? (yes/y для продолжения): ").strip().lower()
    if response not in ['yes', 'y', 'да', 'д']:
        print("[-] Отменено пользователем")
        return 0
    
    print()
    
    # Запуск прошивки
    flasher = XiaomiFlasher(router_ip, username, password, firmware_path)
    success = flasher.run()
    
    print()
    if success:
        print("[✓] Процесс завершен успешно!")
        print()
        print("Что дальше:")
        print("  1. Подождите 2-3 минуты пока роутер загрузится")
        print("  2. Откройте браузер и перейдите на http://192.168.31.1")
        print("  3. Настройте роутер заново")
        return 0
    else:
        print("[✗] Процесс завершился с ошибками")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n\n[-] Прервано пользователем")
        exit_code = 1
    except Exception as e:
        print(f"\n\n[-] Критическая ошибка: {e}")
        exit_code = 1
    
    print()
    input("Нажмите Enter для выхода...")
    sys.exit(exit_code)
