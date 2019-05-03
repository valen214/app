#!/bin/python

# ps -A

def main():
    import os
    import subprocess
    import sys
    import time
    
    try:
        import threading
    except ImportError:
        import dummy_threading as threading
        
    
    parent = os.path.abspath(os.path.join(
            os.path.abspath(sys.argv[0]), os.pardir))
    app = "app.py"
    
    args = [sys.executable, os.path.join(parent, app)]
    
    _proc = subprocess.Popen(args)
    
    watchlist = ["app.py", "pages/util.py"]
    
    def info():
        info = {}
        for f in watchlist:
            info[f] = os.stat(f).st_mtime
        return info
        
    last_info = info()
    def changed():
        nonlocal last_info
        if last_info != info():
            last_info = info()
            return True
        return False
    
    running = True
    def run():
        nonlocal _proc, running
        print("\33[1;32;40m" + "====" * 20)
        print("main.py: app.py bootstrap, listening to changes")
        print("====" * 20 + "\33[0m")

        while running:
            if changed():
                print("\33[1;32;40m" + "====" * 20)
                print("changes in watchlist dectected. rebooting...")
                
                _proc.kill()
                _proc.wait() # return code
                print(f"return code: {_proc.returncode}")
                print("====" * 20 + "\33[0m")
                _proc = subprocess.Popen(args)
            time.sleep(5)
        
    # threading.Thread(target=run).start()
    # running = False
    try:
        run()
    except KeyboardInterrupt:
        print("exit signal received, terminating...")
        running = False
        _proc.wait()
        _proc.kill()
    
if __name__ == "__main__":
    main()
    