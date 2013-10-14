import cProfile
import traps

cProfile.run('traps.view.startApp()', 'profile.dat')
