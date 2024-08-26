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
export const DateTimeDisplay: React.FC<{
  date: string;
  mode: 'short' | 'long';
  displayMillis?: boolean;
}> = (props) => {
  const displayDateTime = new Date(props.date).toLocaleString('en-US', {
    day: 'numeric',
    month: props.mode === 'short' ? 'numeric' : 'long',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: 'numeric',
    fractionalSecondDigits: props.displayMillis ? 3 : undefined,
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
const formatDuration = (duration: number) => {
  const msInSecond = 1_000;
  const msInMinute = 60_000;
  const msInHour = 3_600_000;
  const msInDay = 86_400_000;

  if (duration < msInSecond) {
    return `${duration} ms`;
  }

  const days = Math.floor(duration / msInDay);
  duration %= msInDay;

  const hours = Math.floor(duration / msInHour);
  duration %= msInHour;

  const minutes = Math.floor(duration / msInMinute);
  duration %= msInMinute;

  const seconds = duration / msInSecond;

  const ms = duration % msInSecond;

  if (days > 0) {
    return `${days} d ${hours} h`;
  }

  if (hours > 0) {
    return `${hours} h ${minutes} m`;
  }

  if (minutes > 0) {
    return `${minutes} m ${seconds.toFixed(3)} s`;
  }

  if (seconds > 0) {
    return `${seconds} s`;
  }

  return `${ms} s`;
};

/**
 * Displays a duration for use in a table
 */
export const DurationDisplay: React.FC<{
  startDate: string | number;
  endDate: string | number;
  clsNames?: string;
}> = (props) => {
  const duration = new Date(props.endDate).getTime() - new Date(props.startDate).getTime();
  const formattedDuration = formatDuration(duration);

  return <span className={`whitespace-nowrap text-sm ${props.clsNames}`}>{formattedDuration}</span>;
};
