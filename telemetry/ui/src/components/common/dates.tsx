/**
 * Displays a date in a human-readable format
 */
export const DateDisplay: React.FC<{ date: string }> = ({ date }) => {
  const displayDate = new Date(date).toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  return <span className="whitespace-nowrap text-sm text-gray-500">{displayDate}</span>;
};

/**
 * Displays a datetime in a human-readable format
 */
export const DateTimeDisplay: React.FC<{ date: string; mode: 'short' | 'long' }> = (props) => {
  const displayDateTime = new Date(props.date).toLocaleString('en-US', {
    day: 'numeric',
    month: props.mode === 'short' ? 'numeric' : 'long',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: 'numeric',
    hour12: true // Use AM/PM format. Set to false for 24-hour format.
  });

  return <span className="whitespace-nowrap text-sm text-gray-500">{displayDateTime}</span>;
};

export const TimeDisplay: React.FC<{ date: string }> = ({ date }) => {
  const displayTime = new Date(date).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: 'numeric',
    hour12: true // Use AM/PM format. Set to false for 24-hour format.
  });

  return <span className="whitespace-nowrap text-sm text-gray-500">{displayTime}</span>;
};

/**
 * Formats a duration in a human-readable format.
 * Works for durations in milliseconds, seconds, and microseconds,
 * which is the expected size of durations in the backend.
 */
const formatDuration = (duration: number) => {
  if (duration < 1) {
    return '<1 ms';
  }
  if (duration < 1000) {
    return `${duration} ms`;
  } else if (duration < 1000000) {
    return `${(duration / 1000).toFixed(2)} s`;
  } else {
    return `${(duration / 1000000).toFixed(2)} μs`;
  }
};

/**
 * Displays a duration for use in a table
 */
export const DurationDisplay: React.FC<{ startDate: string; endDate: string }> = (props) => {
  const duration = new Date(props.endDate).getTime() - new Date(props.startDate).getTime();
  const formattedDuration = formatDuration(duration);

  return <span className="whitespace-nowrap text-sm text-gray-500">{formattedDuration}</span>;
};
