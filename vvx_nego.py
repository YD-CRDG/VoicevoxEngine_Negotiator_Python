import atexit
import requests
import json
import winsound
import socket
import subprocess
import os
import time
import io
import zipfile
import base64


class VoicevoxNegotiation:
    #コンストラクト時、指定したアドレスとポートでエンジンを起動する
    def __init__(self, engine_path, address = "127.0.0.1", port = 50021):
        self.VVN_OK = 0
        self.VVN_GENERAL_ERROR = 1
        self.VVN_FAILD_TO_REACH = 2
        self.VVN_MORA_BOTH = 0
        self.VVN_MORA_LENGTH = 1
        self.VVN_MORA_PITCH = 2
        self.vvengine = []
        
        self.audio_query = {}
        self.synthesis = bytes(0)
        self.multi_synthesis_zip = []
        self.multi_synthesis = []
        self.multi_synthesis_name = []
        self.accent_phrases = {}
        self.mora_data = {}
        self.version = ""
        self.preset = {}
        self.speakers = {}
        self.speaker_info ={}

        if self.start_voicevox_engine(engine_path, address, port, enable_print=True) == self.VVN_OK:
            None
        else:
            print("キーを入力するとプログラムを終了します")
            input()
            exit()
    ############################################################################################################################################################################
    #Initalize

    #Voicevoxエンジン起動処理
    #既にポートが塞がっていた場合実行中のエンジンが有る想定でエンジンの起動をスキップする
    def start_voicevox_engine(self, engine_path, address="127.0.0.1", port=50021, enable_print=False):
        self.port = port
        self.address = address
        self.VVE_Url = "http://"+address+":"+str(port)
        print("通信アドレス>>>"+self.VVE_Url)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0.5)
        try:
            client.connect((address, port))
            client.close()
            if enable_print == True: print("ポートが既に使用されています。エンジンが起動済みであるものとして実行します。")
        except:
            client.close()
            if enable_print == True: print("Voicevoxエンジンを起動します。id("+str(len(self.vvengine))+")")
            self.vvengine.append(subprocess.Popen((engine_path, "--port", str(self.port), "--host", self.address)))
            atexit.register(self.terminate_all_engine)
        if self.check_engine_alive() == self.VVN_OK:
            if enable_print == True:
                print("エンジンの稼働を確認しました。")
                print("実行中のバージョン>>>"+self.version)
            return self.VVN_OK
        else:
            if enable_print == True: print("エンジンの起動に失敗しました。")
            return self.VVN_FAILD_TO_REACH


    def check_engine_alive(self, timeout=10):
        timest= time.time()
        while True:
            if time.time() - timest <timeout:
                if self.request_version() == self.VVN_OK:
                    return self.VVN_OK
                time.sleep(0.1)
            else:
                return self.VVN_FAILD_TO_REACH


    #プログラム終了時にサブプロセスで実行中のエンジンを停止するための関数
    def terminate_engine(self, id):
        try:
            self.vvengine[id].terminate()
            print("engine id("+str(id)+") is terminated")
        except AttributeError:
            print("no engine to terminate")

    def terminate_all_engine(self):
        try:
            for engine in self.vvengine:
                engine.terminate()
            print("all engine is terminated")
        except AttributeError:
            print("no engine to terminate")
    
    ############################################################################################################################################################################
    #Querys

    #オーディオクエリの請求
    def request_audio_query(self, text, speaker):
        payload = {"text":text, "speaker":str(speaker)}
        headers = {"accept": "application/json"}
        try:
            response = requests.post(self.VVE_Url+"/audio_query", params=payload, headers=headers)
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.audio_query = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR

    #プリセットを元にしたオーディオクエリの請求
    def request_audio_query_from_preset(self, text, preset):
        payload = {"text":text, "speaker":str(preset)}
        headers = {"accept": "application/json"}
        try:
            response = requests.post(self.VVE_Url+"/audio_query_from_preset", params=payload, headers=headers)
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.audio_query = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR
    ############################################################################################################################################################################
    #Accents

    #AquesTalk風文法を元にアクセント句の要求
    def request_accent_phrases(self, text, speaker , is_kana):
        payload = {"text":text, "speaker":str(speaker), "is_kana":str(is_kana)}
        headers = {"accept": "application/json"}
        try:
            response = requests.post(self.VVE_Url+"/accent_phrases", params=payload, headers=headers)
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.accent_phrases = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR
    
    #Mora(アクセント句)を指定したSpeakerで再設定
    #type：VVN_MORA_BOTH　Moraの長さと高さ双方に適応
    #type：VVN_MORA_LENGTH　Moraの長さだけに適応
    #type：VVN_MORA_PITCH　Moraの高さだけにに適応
    def request_mora_data(self, accent_phrases, speaker, type):
        if type == self.VVN_MORA_BOTH:
            link = "/mora_data"
        elif type == self.VVN_MORA_LENGTH:
            link = "/mora_length"
        elif type == self.VVN_MORA_PITCH:
            link = "/mora_pitch"
        else:
            return self.VVN_GENERAL_ERROR    
        payload = {"speaker":speaker}
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        try:
            response = requests.post(self.VVE_Url+link, params=payload, headers=headers, data=json.dumps(accent_phrases))
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.mora_data = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR
    ############################################################################################################################################################################
    #Synthesis

    #指定したオーディオクエリを元に指定したSpeakerで音声を合成
    #enable_interrogative_upspeak=Trueにすると疑問形の際語尾を自動調整
    def request_synthesis(self, audio_query, speaker, enable_interrogative_upspeak=False):
        payload = {"speaker": str(speaker), "enable_interrogative_upspeak": str(enable_interrogative_upspeak)} 
        headers = {"accept": "audio/wav", "Content-Type": "application/json"}
        try:
            response = requests.post(self.VVE_Url+"/synthesis", params=payload, headers=headers, data=json.dumps(audio_query), stream=True)
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.synthesis = response.content
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR

    #指定したaudio_queryのリストを一気に合成させる
    #結果はmulti_synthesisリストに格納される
    def request_multi_synthesis(self, multi_audio_query, speaker):
        payload = {"speaker": str(speaker)} 
        headers = {"accept": "application/zip", "Content-Type": "application/json"}
        try:
            response = requests.post(self.VVE_Url+"/multi_synthesis", params=payload, headers=headers, data=json.dumps(multi_audio_query), stream=True)
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.multi_synthesis_zip = response.content
            zip = zipfile.ZipFile(io.BytesIO(response.content))
            self.multi_synthesis = [0] * len(zip.namelist())
            self.multi_synthesis_name = zip.namelist()
            for index, name in enumerate(zip.namelist()):
                self.multi_synthesis[index] = zip.read(name)
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR
    
    #指定したオーディオクエリを元に二人のSpeakerの音声をmorph_rateの割合で合成した音声を生成
    def request_synthesis_morphing(self, audio_query, base_speaker, target_speaker, morph_rate):
        payload = {"base_speaker": str(base_speaker), "target_speaker": str(target_speaker), "morph_rate": morph_rate} 
        headers = {"accept": "audio/wav", "Content-Type": "application/json"}
        response = requests.post(self.VVE_Url+"/synthesis_morphing", params=payload, headers=headers, data=json.dumps(audio_query), stream=True)
        if response.status_code == 200:
            self.synthesis = response.content
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR
    ############################################################################################################################################################################
    #Utils

    def request_connect_waves(self, multi_synthesis):
        headers = {"accept": "audio/wav", "Content-Type": "application/json"}
        b64encoded = [bytes(0)] * len(multi_synthesis)
        for index, wav in enumerate(multi_synthesis):
            b64encoded[index] = base64.b64encode(wav).decode("ascii")
        try:
            response = requests.post(self.VVE_Url+"/connect_waves", headers=headers, data=json.dumps(b64encoded), stream=True)
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.synthesis = response.content
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR
    
    #生成した音声(指定したSynthesis)のデータを再生
    def local_play_synthesis(self, synthesis):
        winsound.PlaySound(synthesis, winsound.SND_MEMORY)
    ############################################################################################################################################################################
    #Info_gets

    #エンジンのバージョンを取得
    def request_version(self):
        headers = {"accept": "application/json"}
        try:
            response = requests.get(self.VVE_Url+"/version", headers=headers)
        except:
            return self.VVN_GENERAL_ERROR
        if response.status_code == 200:
            self.version = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR

    #エンジンのプリセット情報を取得
    def request_presets(self):
        headers = {"accept": "application/json"}
        try:
            response = requests.get(self.VVE_Url+"/presets")
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.preset = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR

    #エンジンのキャラクター情報の取得
    def request_speakers(self):
        headers = {"accept": "application/json"}
        try:
            response = requests.get(self.VVE_Url+"/speakers")
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.speakers = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR

    #キャラクターの詳細情報の取得
    def request_speaker_info(self, uuid):
        payload = {"speaker_uuid": uuid}
        headers = {"accept": "application/json"}
        try:
            response = requests.get(self.VVE_Url+"/speaker_info", params=payload, headers=headers)
        except:
            return self.VVN_FAILD_TO_REACH
        if response.status_code == 200:
            self.speaker_info = response.json()
            return self.VVN_OK
        else:
            return self.VVN_GENERAL_ERROR
    ############################################################################################################################################################################
    #Exports

    #pathに生成した音声(指定したSynthesis)のデータを保存
    def local_export_synthesis_wav(self, synthesis, path):
        dat = open(path, "wb")
        dat.write(synthesis)
        dat.close()

    #Pathに指定したフォルダに音声(指定したSynthesisリスト)のデータを
    #指定した名前(Synthesis_nameリストの中身)で保存
    #フォルダがなければ勝手に作る
    def local_export_multi_synthesis_wav(self, multi_synthesis, multi_synthesis_name, folder_path):
        os.makedirs(folder_path, exist_ok=True)
        for index, wav in enumerate(multi_synthesis):
            dat = open(folder_path+"\\"+multi_synthesis_name[index], "wb")
            dat.write(wav)
            dat.close()