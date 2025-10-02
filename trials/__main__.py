"""CLI entry point for trials package."""

import sys

if __name__ == "__main__":
    # Determine which module to run based on first argument
    if len(sys.argv) < 2:
        print("Usage: python -m trials <command>")
        print("Commands: fetch, normalize, eligibility, features, cluster, risk, app")
        sys.exit(1)

    command = sys.argv[1]
    # Remove the command from argv so submodules see correct args
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if command == "fetch":
        from trials.fetch import main
        main()
    elif command == "normalize":
        from trials.normalize import main
        main()
    elif command == "eligibility":
        from trials.eligibility import main
        main()
    elif command == "features":
        from trials.features import main
        main()
    elif command == "cluster":
        from trials.cluster import main
        main()
    elif command == "risk":
        from trials.risk import main
        main()
    elif command == "app":
        import streamlit.web.cli as stcli
        from trials import app
        sys.argv = ["streamlit", "run", app.__file__]
        sys.exit(stcli.main())
    else:
        print(f"Unknown command: {command}")
        print("Commands: fetch, normalize, eligibility, features, cluster, risk, app")
        sys.exit(1)
