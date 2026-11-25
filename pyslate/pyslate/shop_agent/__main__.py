import sys

if len(sys.argv) > 1 and sys.argv[1] == "hud":
    from .hud import main as hud_main

    raise SystemExit(hud_main(sys.argv[2:]))

from .agent import main

raise SystemExit(main())
