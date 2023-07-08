import time, threading

class Background:
  """
  A simple background task manager that considers doing a background task every n seconds. 
  The task is only done if the manager has been marked as pending.
  """
  def __init__(self, method, sleeptime) -> None:
    """
    Create a manager that will consider calling `method` every `sleeptime` seconds
    """
    self.method = method
    self.sleeptime = sleeptime
    self._pending = False
    self._started = False
    self.lock = threading.Lock()

  def start(self):
    """
    Start the manager's thread
    """
    with self.lock:
      if not self._started:
        threading.Thread(group=None, target=self._action, daemon=True).start()
        self._started = True

  def set_pending(self, pending=True):
    """
    Set the task as pending. Next time the manager checks it will call `method` and then unset pending.
    """
    with self.lock:
        self._pending = pending

  def _action(self):
    while True:
      with self.lock:
        if self._pending:
            self.method()
            self._pending = False
      time.sleep(self.sleeptime) 
