# app
An ongoing website with the collections of ideas or sudden thought.


run the server with `python main.py` or `python app.py`

`main.py` is a wrapper that auto updates/reboot when changes detected in source file

currently working on `draw_and_guess.htm`, which does what its name suggests.
The app utilized **`WebRTC`**, a fairly new p2p protocol on the web/javascript.

most interactive pages won't work without start the server (`app.py`) at base directory,
as it includes some path redirecting,
but of course static html pages work just fine.
Might consider improving this for portability,
but actually this project has been rebooted so many times therefore might not be changed in the near future.

