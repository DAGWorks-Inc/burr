import { BookOpenIcon, PencilIcon } from '@heroicons/react/24/outline';
import { ActionModel } from '../../../api';
import { ChipGroup } from '../../common/chip';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { base16AteliersulphurpoolLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

/**
 * Renders the code for an action.
 * Note that if you turn on numbering the behavior can get really strange
 *
 */
export const CodeView = (props: { code: string }) => {
  return (
    <div className="h-full w-full pt-2 gap-2 flex flex-col max-w-full overflow-y-auto">
      <SyntaxHighlighter
        language="python"
        className="bg-dwdarkblue/100 hide-scrollbar"
        wrapLines={true}
        wrapLongLines={true}
        style={base16AteliersulphurpoolLight}
      >
        {props.code}
      </SyntaxHighlighter>
    </div>
  );
};
/**
 * Renders the view of the action -- this has some indications of reading/writing state.
 * Currently we don't have inputs, but we will add that in the future.
 *
 * TODO -- add inputs
 */
export const ActionView = (props: { currentAction: ActionModel | undefined }) => {
  if (props.currentAction === undefined) {
    return <div></div>;
  }
  const reads = props.currentAction.reads;
  const writes = props.currentAction.writes;
  const name = props.currentAction.name;

  return (
    <div className="h-full w-full pl-1 pt-2 gap-2 flex flex-col">
      <h1 className="text-2xl text-gray-600 font-semibold">{name}</h1>
      <ChipGroup
        chips={reads}
        type="stateRead"
        label={<BookOpenIcon className="h-6 w-6 text-gray-500" />}
      />
      <ChipGroup
        chips={writes}
        type="stateWrite"
        label={<PencilIcon className="h-6 w-6 text-gray-500" />}
      />
      <CodeView code={props.currentAction.code} />
    </div>
  );
};
