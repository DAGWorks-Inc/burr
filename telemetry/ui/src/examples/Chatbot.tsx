import { ComputerDesktopIcon, UserIcon } from '@heroicons/react/24/outline';
import { classNames } from '../utils/tailwind';
import { Button } from '../components/common/button';
import { TwoColumnLayout } from '../components/common/layout';
import { MiniTelemetry } from './MiniTelemetry';
import { ApplicationSummary, ChatItem, DefaultService } from '../api';
import { KeyboardEvent, useEffect, useState } from 'react';
import { useMutation, useQuery } from 'react-query';
import { Loading } from '../components/common/loading';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DateTimeDisplay } from '../components/common/dates';
import AsyncCreatableSelect from 'react-select/async-creatable';

type Role = 'assistant' | 'user';

const DEFAULT_CHAT_HISTORY: ChatItem[] = [
  {
    role: ChatItem.role.ASSISTANT,
    content:
      '📖 Select a conversation from the list to get started! ' +
      'The left side of this is a simple chatbot. The right side is the same' +
      ' Burr Telemetry app you can see if you click through the [chatbot demo](/projects/demo:chatbot) project. Note that images ' +
      "will likely stop displaying after a while due to OpenAI's persistence policy. So generate some new ones! 📖",
    type: ChatItem.type.TEXT
  },
  {
    role: ChatItem.role.ASSISTANT,
    content:
      ' \n\n💡 This is meant to demonstrate the power of the Burr model -- ' +
      'chat on the left while examining the internals of the chatbot on the right.💡',
    type: ChatItem.type.TEXT
  }
];

const getCharacter = (role: Role) => {
  return role === 'assistant' ? 'AI' : 'You';
};

const RoleIcon = (props: { role: Role }) => {
  const Icon = props.role === 'assistant' ? ComputerDesktopIcon : UserIcon;
  return (
    <Icon className={classNames('text-gray-400', 'ml-auto h-6 w-6 shrink-0')} aria-hidden="true" />
  );
};

const LAST_MESSAGE_ID = 'last-message';

const ImageWithBackup = (props: { src: string; alt: string }) => {
  const [caption, setCaption] = useState<string | undefined>(undefined);
  return (
    <div>
      <img
        src={props.src}
        alt={props.alt}
        onError={(e) => {
          const img = e.target as HTMLImageElement;
          img.src = 'https://via.placeholder.com/500x500?text=Image+Unavailable';
          img.alt =
            'Image unavailable as OpenAI does not persist images -- generate a new one, or modify the code to save it for you.';
          setCaption(img.alt);
        }}
      />
      {caption && <span className="italic text-gray-300">{caption}</span>}
    </div>
  );
};
const ChatMessage = (props: { message: ChatItem; id?: string }) => {
  return (
    <div className="flex gap-3 my-4  text-gray-600 text-sm flex-1 w-full" id={props.id}>
      <span className="relative flex shrink-0">
        <RoleIcon role={props.message.role} />
      </span>
      <p className="leading-relaxed w-full">
        <span className="block font-bold text-gray-700">{getCharacter(props.message.role)} </span>
        {props.message.type === ChatItem.type.TEXT ||
        props.message.type === ChatItem.type.CODE ||
        props.message.type === ChatItem.type.ERROR ? (
          <Markdown
            components={{
              // Custom rendering for links
              a: ({ ...props }) => <a className="text-dwlightblue hover:underline" {...props} />
            }}
            remarkPlugins={[remarkGfm]}
            className={`whitespace-pre-wrap break-lines max-w-full ${props.message.type === ChatItem.type.ERROR ? 'bg-dwred/10' : ''} p-0.5`}
          >
            {props.message.content}
          </Markdown>
        ) : (
          <ImageWithBackup src={props.message.content} alt="chatbot image" />
        )}
      </p>
    </div>
  );
};

const scrollToLatest = () => {
  const lastMessage = document.getElementById(LAST_MESSAGE_ID);
  if (lastMessage) {
    const scroll = () => {
      lastMessage.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
    };
    scroll();
    const observer = new ResizeObserver(() => {
      scroll();
    });
    observer.observe(lastMessage);
    setTimeout(() => observer.disconnect(), 1000); // Adjust timeout as needed
  }
};

export const Chatbot = (props: { projectId: string; appId: string | undefined }) => {
  const [currentPrompt, setCurrentPrompt] = useState<string>('');
  const [displayedChatHistory, setDisplayedChatHistory] = useState(DEFAULT_CHAT_HISTORY);
  const { isLoading } = useQuery(
    // TODO -- handle errors
    ['chat', props.projectId, props.appId],
    () =>
      DefaultService.chatHistoryApiV0ChatbotResponseProjectIdAppIdGet(
        props.projectId,
        props.appId || '' // TODO -- find a cleaner way of doing a skip-token like thing here
      ),
    {
      enabled: props.appId !== undefined,
      onSuccess: (data) => {
        setDisplayedChatHistory(data); // when its succesful we want to set the displayed chat history
      }
    }
  );

  // Scroll to the latest message when the chat history changes
  useEffect(() => {
    scrollToLatest();
  }, [displayedChatHistory]);

  const mutation = useMutation(
    (message: string) => {
      return DefaultService.chatResponseApiV0ChatbotResponseProjectIdAppIdPost(
        props.projectId,
        props.appId || '',
        message
      );
    },
    {
      onSuccess: (data) => {
        setDisplayedChatHistory(data);
      }
    }
  );

  if (isLoading) {
    return <Loading />;
  }
  const sendPrompt = () => {
    if (currentPrompt !== '') {
      mutation.mutate(currentPrompt);
      setCurrentPrompt('');
      setDisplayedChatHistory([
        ...displayedChatHistory,
        {
          role: ChatItem.role.USER,
          content: currentPrompt,
          type: ChatItem.type.TEXT
        }
      ]);
    }
  };
  const isChatWaiting = mutation.isLoading;
  return (
    <div className="mr-4 bg-white  w-full flex flex-col h-full">
      <h1 className="text-2xl font-bold px-4 text-gray-600">{'Learn Burr '}</h1>
      <h2 className="text-lg font-normal px-4 text-gray-500 flex flex-row">
        The chatbot below is implemented using Burr. Watch the Burr UI (on the right) change as you
        chat...
      </h2>
      <div className="flex-1 overflow-y-auto p-4 hide-scrollbar">
        {displayedChatHistory.map((message, i) => (
          <ChatMessage
            message={message}
            key={i}
            id={i === displayedChatHistory.length - 1 ? LAST_MESSAGE_ID : undefined}
          ></ChatMessage>
        ))}
      </div>
      <div className="flex items-center pt-4 gap-2">
        <input
          className="flex h-10 w-full rounded-md border border-[#e5e7eb] px-3 py-2 text-sm placeholder-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#9ca3af] disabled:cursor-not-allowed disabled:opacity-50 text-[#030712] focus-visible:ring-offset-2"
          placeholder="Ask me how tall the Eifel tower is!"
          value={currentPrompt}
          onChange={(e) => setCurrentPrompt(e.target.value)}
          onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendPrompt();
            }
          }}
          disabled={isChatWaiting || props.appId === undefined}
        />
        <Button
          className="w-min cursor-pointer h-full"
          color="dark"
          disabled={isChatWaiting || props.appId === undefined}
          onClick={() => {
            sendPrompt();
          }}
        >
          Send
        </Button>
      </div>
    </div>
  );
};

export const TelemetryWithSelector = (props: {
  projectId: string;
  currentApp: ApplicationSummary | undefined;
  setCurrentApp: (app: ApplicationSummary) => void;
}) => {
  return (
    <div className="w-full h-[90%]">
      <div className="w-full">
        <ChatbotAppSelector
          projectId={props.projectId}
          setApp={props.setCurrentApp}
          currentApp={props.currentApp}
          placeholder={'Select a conversation or create a new one by typing...'}
        ></ChatbotAppSelector>
      </div>
      <MiniTelemetry projectId={props.projectId} appId={props.currentApp?.app_id}></MiniTelemetry>
    </div>
  );
};

const Label = (props: { application: ApplicationSummary }) => {
  return (
    <div className="flex flex-row gap-2 items-center justify-between">
      <div className="flex flex-row gap-2 items-center">
        <span className="text-gray-400 w-10">{props.application.num_steps}</span>
        <span>{props.application.app_id}</span>
      </div>
      <DateTimeDisplay date={props.application.first_written} mode="short" />
    </div>
  );
};

export const ChatbotAppSelector = (props: {
  projectId: string;
  setApp: (app: ApplicationSummary) => void;
  currentApp: ApplicationSummary | undefined;
  placeholder: string;
}) => {
  const { projectId, setApp } = props;
  const { data, refetch } = useQuery(
    ['apps', projectId],
    () => DefaultService.getAppsApiV0ProjectIdAppsGet(projectId as string),
    { enabled: projectId !== undefined }
  );
  const createAndUpdateMutation = useMutation(
    (app_id: string) =>
      DefaultService.createNewApplicationApiV0ChatbotCreateProjectIdAppIdPost(projectId, app_id),

    {
      onSuccess: (appID) => {
        refetch().then((data) => {
          const appSummaries = data.data || [];
          const app = appSummaries.find((app) => app.app_id === appID);
          if (app) {
            setApp(app);
          }
        });
      }
    }
  );
  const appSetter = (appID: string) => createAndUpdateMutation.mutate(appID);
  const dataOrEmpty = Array.from(data || []);
  const options = dataOrEmpty
    .sort((a, b) => {
      return new Date(a.last_written) > new Date(b.last_written) ? -1 : 1;
    })
    .map((app) => {
      return {
        value: app.app_id,
        label: <Label application={app} />
      };
    });
  return (
    <AsyncCreatableSelect
      placeholder={props.placeholder}
      cacheOptions
      defaultOptions={options}
      onCreateOption={appSetter}
      value={options.find((option) => option.value === props.currentApp?.app_id) || null}
      onChange={(choice) => {
        const app = dataOrEmpty.find((app) => app.app_id === choice?.value);
        if (app) {
          setApp(app);
        }
      }}
    />
  );
};

export const ChatbotWithTelemetry = () => {
  const currentProject = 'demo_chatbot';
  const [currentApp, setCurrentApp] = useState<ApplicationSummary | undefined>(undefined);

  return (
    <TwoColumnLayout
      firstItem={<Chatbot projectId={currentProject} appId={currentApp?.app_id} />}
      secondItem={
        <TelemetryWithSelector
          projectId={currentProject}
          currentApp={currentApp}
          setCurrentApp={setCurrentApp}
        />
      }
      mode={'third'}
    ></TwoColumnLayout>
  );
};
