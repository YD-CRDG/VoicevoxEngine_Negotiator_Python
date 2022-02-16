import vvx_nego

if __name__ == "__main__":
    #hogeの部分をエンジンが有るpathに変更して実行してください
    vvn = vvx_nego.VoicevoxNegotiation("hoge\\run.exe")
    vvn.request_audio_query("これは", speaker=1)
    vvn.request_synthesis(vvn.audio_query, speaker=1)
    vvn.multi_synthesis.append(vvn.synthesis)

    vvn.request_audio_query("読み上げを実行する", speaker=3)
    vvn.request_synthesis(vvn.audio_query, speaker=3)
    vvn.multi_synthesis.append(vvn.synthesis)

    vvn.request_audio_query("サンプルコードです", speaker=5)
    vvn.request_synthesis(vvn.audio_query, speaker=5)
    vvn.multi_synthesis.append(vvn.synthesis)
    
    vvn.request_connect_waves(vvn.multi_synthesis)
    #音が出ます
    vvn.local_play_synthesis(vvn.synthesis)
    
    input()
