# SublimePackageSync

Checks any git repository out to the sublime packages folder from any git object.


## Why?

This package came about because I wanted the benefits of [Package Control][1], particularily the ease which it provides in keeping packages synced across different machines, but I didn't want to be at the mercy of the original developers maintaining their code and/or accepting pull requests.

With [SublimePackageSync][2], you can keep a package synced to a particular commit, branch, tag, or any other git object of any repository (the original or a fork), and keep that configuration in sync between multiple machines.


## How?

Whenever you start Sublime Text, [SublimePackageSync][2] updates or clones all the repositories you've told it about in the [settings file](#settings).

If you don't want to have to restart to update a package, run the `SublimePackageSync: Sync All` command from the command pallette.

If you only want to update one package, run the `SublimePackageSync: Sync Specific` command and choose the package you want to sync.


### Settings

See `Preferences > SublimePackageSync > Settings - Default` for an example settings file. Copy the file into your `Packages/User` directory before making any changes to avoid them being overwritten by updates.


## Contributions

Bug reports, forks and pull requests are welcome.


[1]: https://sublime.wbond.net
[2]: https://github.com/erbridge/SublimePackageSync
