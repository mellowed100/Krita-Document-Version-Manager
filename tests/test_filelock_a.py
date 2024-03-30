import portalocker
import time


print('opening file.lock')
file = open('file.lock', 'w')

print('locking file')
portalocker.lock(file, portalocker.LOCK_EX)
print('file locked')

print('sleeping')
time.sleep(5)

print('unlocking file')
portalocker.unlock(file)

print('closing file')
file.close()
