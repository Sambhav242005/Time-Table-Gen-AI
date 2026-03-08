import json
import logging
import os
import sys
import traceback

from core.generator_thread import TimetableGeneratorThread


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m core.solver_worker <input_json> <output_json>")
        return 2

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Disable Qt signal emits in subprocess.
        os.environ["TT_DISABLE_EMITS"] = "1"

        solver_thread = TimetableGeneratorThread(config)
        solver_thread._initialize_resources()
        events = solver_thread._prepare_events()
        if not events:
            payload = {
                "ok": False,
                "error": "No events to schedule. Check subject/section assignments.",
            }
        else:
            result = solver_thread._solve_cpsat(events)
            if result is None:
                payload = {
                    "ok": False,
                    "error": (
                        "Could not find a valid timetable.\n"
                        "Try reducing sections or adding more teachers/rooms."
                    ),
                }
            else:
                payload = {"ok": True, "result": result}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return 0
    except Exception as e:
        payload = {"ok": False, "error": f"{e}\n\n{traceback.format_exc()}"}
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
        except Exception:
            logger.exception("Failed to write solver worker output")
        logger.exception("Solver worker failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
