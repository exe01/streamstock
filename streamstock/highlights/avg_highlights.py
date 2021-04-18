from .highlights import Highlights
from streamstock.chat import Chat
from streamstock.chat import Message
from . import Moment
from datetime import timedelta, datetime
from typing import Generator, Optional, List
import logging


class AVGHighlights(Highlights):
    def __init__(self,
                 chat: Chat,
                 tic: timedelta,
                 highlight_percent: float = 0.5,
                 skip_calc_for_firsts_tics: timedelta = timedelta(),
                 max_moment_duration: timedelta = timedelta(minutes=5),
                 add_prehighlight_moment: bool = True):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._chat = chat
        self._tic = tic
        self._highlight_percent = highlight_percent
        self._skip_calc_for_firsts_tics = skip_calc_for_firsts_tics
        self._max_moment_duration = max_moment_duration
        self._add_prehighlight_moment = add_prehighlight_moment

        self._first_msg: Message
        self._begin_of_tic: datetime
        self._end_of_tic: datetime
        self._current_msg: Message
        self._tic_messages: List[Message] = []
        self._count_of_messages = 0
        self._count_of_tic = 0
        self._current_moment: Optional[Moment] = None
        self._prehighlight_moment: Optional[Moment] = None

    @property
    def avg_per_tic(self):
        if self._count_of_tic == 0:
            return 0

        return self._count_of_messages / self._count_of_tic

    def process(self) -> Generator[Moment, None, None]:
        self._update_first_tic()
        self._add_message_to_tic()

        for self._current_msg in self._chat.read():
            if self._msg_in_range_of_tic():
                self._add_message_to_tic()
            else:
                moment = self._create_or_update_moment()
                if moment:
                    yield moment

                self._tic_while_msg_is_not_in_range()
                self._add_message_to_tic()

        moment = self._create_or_update_moment(force_end=True)
        if moment:
            yield moment

    def _create_or_update_moment(self, force_end=False):
        if force_end and self._current_moment:
            return self._produce_moment()
        else:
            if self._tic_is_highlight:
                if self._current_moment:
                    self._update_moment()
                else:
                    self._create_moment()

                if self._current_moment.duration >= self._max_moment_duration:
                    return self._produce_moment()
            else:
                if self._add_prehighlight_moment:
                    self._create_prehighlight_moment()

                if self._current_moment:
                    return self._produce_moment()

    def _create_moment(self):
        if self._prehighlight_moment:
            self._current_moment = self._prehighlight_moment
            self._update_moment()
        else:
            self._current_moment = Moment(start=self._begin_of_tic,
                                          end=self._end_of_tic,
                                          messages=self._tic_messages)

    def _create_prehighlight_moment(self):
        self._prehighlight_moment = Moment(start=self._begin_of_tic,
                                           end=self._end_of_tic,
                                           messages=self._tic_messages)

    def _update_moment(self):
        self._current_moment.end = self._end_of_tic
        self._current_moment.messages.extend(self._tic_messages)

    def _produce_moment(self):
        moment = self._current_moment
        self._current_moment = None
        self._prehighlight_moment = None
        return moment

    def _tic_while_msg_is_not_in_range(self):
        while not self._msg_in_range_of_tic():
            self._next_tic()

    def _update_first_tic(self):
        self._current_msg = next(self._chat.read())
        self._first_msg = self._current_msg

        self._begin_of_tic = self._current_msg.created
        self._end_of_tic = self._begin_of_tic + self._tic

    def _next_tic(self):
        self._print_info()

        self._begin_of_tic += self._tic
        self._end_of_tic = self._begin_of_tic + self._tic

        if not self._skip_tic():
            self._count_of_tic += 1
            self._count_of_messages += len(self._tic_messages)

        self._tic_messages = []

    def _add_message_to_tic(self):
        self._tic_messages.append(self._current_msg)

    def _msg_in_range_of_tic(self):
        return self._begin_of_tic <= self._current_msg.created < self._end_of_tic

    def _print_info(self):
        self._logger.debug('{}-{} Messages per tic: {}\t| AVG: {} \t| Highlight: {}'.format(
            self._begin_of_tic,
            self._end_of_tic,
            len(self._tic_messages),
            round(self.avg_per_tic, 1),
            self._tic_is_highlight
        ))

    def _skip_tic(self):
        return self._first_msg.created + self._skip_calc_for_firsts_tics > self._current_msg.created

    @property
    def _tic_is_highlight(self):
        """AVG per tic is ~50% of avg_max per tic or of ~200% of avg_min per tic.
        """
        if self._skip_tic():
            return True

        return len(self._tic_messages) >= (2 * self.avg_per_tic * self._highlight_percent)
