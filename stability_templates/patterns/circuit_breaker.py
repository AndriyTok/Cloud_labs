import logging
from datetime import datetime, timezone

#standart logging settings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
) #it is important for the timestamps in the logs

#constant states of circuit breaker
class StateChoices:
    OPEN = "open" # the circuit is open and calls are not allowed
    CLOSED = "closed" # the circuit is closed and calls are allowed
    HALF_OPEN = "half_open" # the circuit is half open and a test call is allowed

#special exception for remote call failures (to distinguish all client problems in one place)
class RemoteCallFailedException(Exception):
    pass


class CircuitBreaker:
    def __init__(self, func, exceptions, threshold, delay):
        self.func = func
        self.exceptions_to_catch = exceptions
        self.threshold = threshold #number of failed attempts before opening the circuit
        self.delay = delay
        self.state = StateChoices.CLOSED
        self.last_attempt_timestamp = None
        self._failed_attempt_count = 0

    #additional helper methods
    def update_last_attempt_timestamp(self):
        self.last_attempt_timestamp = datetime.now(timezone.utc).timestamp()

    def set_state(self, state):
        prev_state = self.state
        self.state = state
        logging.info(f"Changed state from {prev_state} to {self.state}")

    #main methods
    #default state handling
    def handle_closed_state(self, *args, **kwargs):
        allowed_exceptions = self.exceptions_to_catch
        try: #if function call is successful
            ret_val = self.func(*args, **kwargs)
            logging.info("Success: Remote call")
            self.update_last_attempt_timestamp()
            self._failed_attempt_count = 0 # reset the failed attempt count
            return ret_val
        except allowed_exceptions as e:
            # remote call has failed
            logging.info("Failure: Remote call")
            # increment the failed attempt count
            self._failed_attempt_count += 1

            # update last_attempt_timestamp
            self.update_last_attempt_timestamp()

            # if the failed attempt count is more than the threshold
            # then change the state to OPEN
            if self._failed_attempt_count >= self.threshold:
                self.set_state(StateChoices.OPEN)
            # re-raise the exception
            raise RemoteCallFailedException from e

    def handle_open_state(self, *args, **kwargs):
        current_timestamp = datetime.now(timezone.utc).timestamp()
        # if `delay` seconds have not elapsed since the last attempt, raise an exception
        if self.last_attempt_timestamp + self.delay >= current_timestamp:
            raise RemoteCallFailedException(f"Retry after {self.last_attempt_timestamp+self.delay-current_timestamp} secs")

        # after `delay` seconds have elapsed since the last attempt, try making the remote call
        # update the state to half open state
        self.set_state(StateChoices.HALF_OPEN)
        allowed_exceptions = self.exceptions_to_catch
        try:
            ret_val = self.func(*args, **kwargs)
            # the remote call was successful
            # now reset the state to Closed
            self.set_state(StateChoices.CLOSED)
            # reset the failed attempt counter
            self._failed_attempt_count = 0
            # update the last_attempt_timestamp
            self.update_last_attempt_timestamp()
            # return the remote call's response
            return ret_val
        except allowed_exceptions as e:
            # the remote call failed again
            # increment the failed attempt count
            self._failed_attempt_count += 1

            # update last_attempt_timestamp
            self.update_last_attempt_timestamp()

            # set the state to "OPEN"
            self.set_state(StateChoices.OPEN)

            # raise the error
            raise RemoteCallFailedException from e

    #dispatcher method
    def make_remote_call(self, *args, **kwargs):
        if self.state == StateChoices.CLOSED:
            return self.handle_closed_state(*args, **kwargs)
        if self.state == StateChoices.OPEN:
            return self.handle_open_state(*args, **kwargs)