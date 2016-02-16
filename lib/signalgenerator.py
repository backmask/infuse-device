class OscillatingSignal(object):

  def __init__(self, begin, end, step):
    self.speed = 1
    self.begin = begin
    self.end = end
    self.step = step
    self.value = begin

  def next(self):
    if callable(self.step):
      self.value += self.step() * self.speed
    else:
      self.value += self.step * self.speed

    if self.value >= self.end:
      self.speed *= -1
      self.value = self.end
    elif self.value <= self.begin:
      self.speed *= -1
      self.value = self.begin

    return self.value
