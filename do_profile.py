import cProfile
import datetime

from hera.main import external_main


now = datetime.datetime.now()
filename = "profile/profile-{0.year}-{0.month:0>2}-{0.day:0>2}-{0.hour:0>2}:{0.minute:0>2}".format(now)
cProfile.run("external_main()")
print("Wrote profile to {}".format(filename))
