import { ClipboardIcon } from '@heroicons/react/24/outline';
import { Step } from '../../../api';
import { useEffect, useState } from 'react';

const FlashMessage = ({
  message,
  duration,
  onClose
}: {
  message: string;
  duration: number;
  onClose: () => void;
}) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className="fixed bottom-4 right-4 bg-dwlightblue text-white p-2 rounded shadow-lg">
      {message}
    </div>
  );
};

export const ReproduceView = (props: {
  step: Step | undefined;
  appId: string;
  partitionKey: string;
  projectID: string;
}) => {
  const cmd =
    'burr-test-case create  \\\n' +
    `  --project-name "${props.projectID}" \\\n` +
    `  --partition-key "${props.partitionKey}" \\\n` +
    `  --app-id "${props.appId}" \\\n` +
    `  --sequence-id ${props.step ? props.step.step_start_log.sequence_id : '?'} \\\n` +
    '  --target-file-name YOUR_FIXTURE_FILE.json \n';

  const [isFlashVisible, setIsFlashVisible] = useState(false);

  return (
    <div className="pt-2 flex flex-col gap-4">
      {isFlashVisible && (
        <FlashMessage
          message="Copied to clipboard!"
          duration={2000}
          onClose={() => setIsFlashVisible(false)}
        />
      )}
      <div className="flex flex-row justify-between text-gray-700">
        <p>
          To generate a test case for this step, run the following command.
          <a
            href="https://burr.dagworks.io/examples/creating_tests/"
            target="_blank"
            rel="noreferrer"
            className="hover:underline text-dwlightblue"
          >
            {' '}
            Further reading
          </a>
          .
        </p>{' '}
        <ClipboardIcon
          className="h-5 w-5 min-h-5 min-w-5 cursor-pointer hover:scale-110"
          onClick={() => {
            navigator.clipboard.writeText(cmd);
            setIsFlashVisible(true);
          }}
        />
      </div>
      <pre className="text-white bg-gray-800 p-2 rounded-md text-sm">{cmd}</pre>
    </div>
  );
};
