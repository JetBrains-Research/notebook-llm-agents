import re
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Generator

import pandas as pd
import streamlit as st
import yaml

with open("app/config_avatar_logos.yaml", "r") as file:
    role_avatars = yaml.safe_load(file)


def check_session_variables(variables: dict) -> None:
    for var, value in variables.items():
        if var not in st.session_state:
            setattr(st.session_state, var, value)


def get_last_line(log_file_path: Path) -> str:
    with log_file_path.open("r") as f:
        lines = f.readlines()
        return lines[-1] if lines else None


def file_update_check(log_file_path: Path = Path("logs/log.log"), sleep_time: float = 0.01):
    while True:
        if line := get_last_line(log_file_path):
            yield line

        time.sleep(sleep_time)


class Level(Enum):
    INFO = 1


class ActionType(Enum):
    START_SESSION = 1
    ACTION = 2
    ERROR = 3
    INTERNAL_ERROR = 4
    STEP = 5
    FUNC = 6
    CONTEXT = 7
    SOLVED = 8
    FINISH_SESSION = 9


class LogLine:
    def __init__(self, line):
        self.raw_line = line
        self.time = None
        self.level = None
        self.action_type = None
        self.source = ""
        self.parse_line()

    def parse_line(self):
        pattern = r"^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}):(\w+):\[(\w+)\](.*)$"
        match = re.match(pattern, self.raw_line)
        if match:
            date_str, level_str, action_str, src_str = match.groups()
            self.time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S,%f")
            self.level = Level[level_str]
            self.action_type = ActionType[action_str]
            self.source = src_str.strip()

    def to_series(self):
        return pd.Series(
            {
                "time": self.time,
                "level": self.level,
                "action_type": self.action_type,
                "source": self.source,
                "raw_message": self.raw_line,
            }
        )


VARIABLES = {"logs": [], "context": [], "run": True}

check_session_variables(VARIABLES)


def reset_chat():
    st.session_state.logs = []
    st.session_state.context = []
    st.session_state.run = True

    st.rerun()


def display_chat():
    for log in st.session_state.logs:
        display_message(log)


def display_message(log: pd.Series):
    role = "ai" if log.action_type == ActionType.FUNC else "user"

    action_map = {
        ActionType.FUNC: st.json,
        ActionType.SOLVED: st.success,
        ActionType.ERROR: st.error,
        ActionType.INTERNAL_ERROR: st.error,
    }

    with st.chat_message(name=role, avatar=role_avatars[role]):
        action_map.get(log.action_type, st.write)(log.source)


def live_chat(gen: Generator):
    last_message = next(gen)
    if not len(st.session_state.logs) or last_message != st.session_state.logs[-1]["raw_message"]:
        log = LogLine(last_message).to_series()

        if log.action_type == ActionType.START_SESSION:
            reset_chat()
        elif log.action_type == ActionType.FINISH_SESSION and len(st.session_state.logs) > 1:
            st.session_state.run = False
        elif log.action_type == ActionType.CONTEXT:
            return

        if not log.source:
            return

        display_message(log)
        st.session_state.logs.append(log)


def live_context(gen: Generator):
    last_message = next(gen)
    if not len(st.session_state.context) or last_message != st.session_state.context[-1]["raw_message"]:
        log = LogLine(last_message).to_series()

        if log.action_type in [ActionType.CONTEXT, ActionType.FUNC]:
            if not log.source:
                return

            role = "ai"
            with st.chat_message(name=role, avatar=role_avatars[role]):
                message = log.source.replace("<line_sep>", "\n\n")
                max_log_source = 150
                msg_processor = st.json if log.action_type == ActionType.FUNC else st.write
                if len(message) < max_log_source:
                    msg_processor(message)
                else:
                    with st.expander("Additional context"):
                        msg_processor(message)

            st.session_state.context.append(log)


st.set_page_config(layout="wide")


def main():
    st.title("Notebook-Agent Interaction")
    log_file_path = Path("logs/actions.log")
    log_gen = file_update_check(log_file_path)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Agent's Context")
        live_context(log_gen)
    with col2:
        st.subheader("Logs")
        live_chat(log_gen)

    while st.session_state.run:
        with col1:
            live_context(log_gen)

        with col2:
            live_chat(log_gen)


if __name__ == "__main__":
    main()
