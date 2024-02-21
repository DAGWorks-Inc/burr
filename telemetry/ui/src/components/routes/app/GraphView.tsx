import { ActionModel, ApplicationModel, Step } from '../../../api';

import ELK from 'elkjs/lib/elk.bundled.js';
import React, { createContext, useCallback, useLayoutEffect, useRef, useState } from 'react';
import ReactFlow, {
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlowProvider,
  useReactFlow
} from 'reactflow';

import 'reactflow/dist/style.css';
import { backgroundColorsForIndex } from './AppView';
import { getActionStatus } from '../../../utils';
import SmartBezierEdge from '@tisoap/react-flow-smart-edge';

const elk = new ELK();

const elkOptions = {
  'elk.algorithm': 'layered',
  'elk.layered.spacing.nodeNodeBetweenLayers': '100',
  'elk.spacing.nodeNode': '80',
  'org.eclipse.elk.alg.layered.options.CycleBreakingStrategy': 'GREEDY',
  'org.eclipse.elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
  // 'org.eclipse.elk.layered.feedbackEdges': 'true',
  'org.eclipse.elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP'
};

type NodeData = {
  action: ActionModel;
  label: string;
};
type NodeType = {
  id: string;
  type: string;
  data: NodeData;
  position: {
    x: number;
    y: number;
  };
};

type EdgeType = {
  id: string;
  source: string;
  target: string;
  markerEnd: {
    type: MarkerType;
    width: number;
    height: number;
  };
};

const ActionNode = (props: { data: NodeData }) => {
  const {
    highlightedActions: previousActions,
    hoverAction,
    currentAction
  } = React.useContext(NodeStateProvider);
  // const bgColor = highlightedActions?.includes(props.data.action.name) ? 'bg-dwlightblue' : '';
  const highlightedActions = [currentAction, ...(previousActions || [])];
  const indexOfAction = highlightedActions.findIndex(
    (step) => step?.step_start_log.action === props.data.action.name
  );
  const step = highlightedActions[indexOfAction];
  const isCurrentAction = indexOfAction === 0;
  const bgColor =
    step !== undefined ? backgroundColorsForIndex(indexOfAction, getActionStatus(step)) : '';
  const opacity = hoverAction?.step_start_log.action === props.data.action.name ? 'opacity-50' : '';
  const additionalClasses = isCurrentAction ? 'border-5 border-dwdarkblue/60 text-white' : '';
  return (
    <>
      <Handle type="target" position={Position.Top} />
      <div
        className={`${bgColor} ${opacity} ${additionalClasses} text-lg font-sans  p-3 rounded-md border-dwlightblue b-2 border`}
      >
        {props.data.action.name}
      </div>
      <Handle type="source" position={Position.Bottom} id="a" />
    </>
  );
};

const getLayoutedElements = (
  nodes: NodeType[],
  edges: EdgeType[],
  options: { [key: string]: string } = {}
) => {
  const isHorizontal = options?.['elk.direction'] === 'RIGHT';
  const nodeNameMap = nodes.reduce(
    (acc, node) => {
      acc[node.id] = node;
      return acc;
    },
    {} as { [key: string]: NodeType }
  );
  const graph = {
    id: 'root',
    layoutOptions: options,
    children: nodes.map((node) => ({
      ...node,
      // Adjust the target and source handle positions based on the layout
      // direction.
      targetPosition: isHorizontal ? 'left' : 'top',
      sourcePosition: isHorizontal ? 'right' : 'bottom',

      // Hardcode a width and height for elk to use when layouting.
      width: 150,
      height: 100
    })),
    edges: edges.map((edge) => {
      console.log(edge, nodeNameMap[edge.source], nodeNameMap[edge.target]);
      return {
        ...edge,
        sources: [edge.source],
        targets: [edge.target]
      };
    })
  };
  return elk.layout(graph).then((layoutedGraph) => ({
    nodes: (layoutedGraph.children || []).map((node) => {
      const originalNode = nodeNameMap[node.id];
      return {
        ...originalNode,
        position: {
          x: node.x as number,
          y: node.y as number
        }
      };
    }),
    edges: (layoutedGraph?.edges || []).map((edge) => {
      return {
        ...edge,
        markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20 },
        source: edge.sources[0],
        target: edge.targets[0]
      };
    })
  }));
};

const convertApplicationToGraph = (stateMachine: ApplicationModel): [NodeType[], EdgeType[]] => {
  return [
    stateMachine.actions.map((action) => ({
      id: action.name,
      type: 'action',
      data: { action, label: action.name },
      position: { x: 0, y: 0 }
    })),
    stateMachine.transitions.map((transition) => ({
      id: `${transition.from_}-${transition.to}-${transition.condition}`,
      source: transition.from_,
      target: transition.to,
      markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20 }
    }))
  ];
};

const nodeTypes = {
  action: ActionNode
};

const edgeTypes = {
  default: SmartBezierEdge
};

type NodeState = {
  highlightedActions: Step[] | undefined; // one for each highlighted action, in order from most recent to least recent
  hoverAction: Step | undefined; // the action currently being hovered over
  currentAction: Step | undefined; // the action currently being viewed
};
const NodeStateProvider = createContext<NodeState>({
  highlightedActions: undefined,
  hoverAction: undefined,
  currentAction: undefined
});

export const _Graph = (props: {
  stateMachine: ApplicationModel;
  currentAction: Step | undefined;
  previousActions: Step[] | undefined;
  hoverAction: Step | undefined;
}) => {
  const [initialNodes, initialEdges] = React.useMemo(() => {
    return convertApplicationToGraph(props.stateMachine);
  }, [props.stateMachine]);

  const [nodes, setNodes] = useState<NodeType[]>([]);
  const [edges, setEdges] = useState<EdgeType[]>([]);

  const { fitView } = useReactFlow();

  const onLayout = useCallback(
    ({ direction = 'UP', useInitialNodes = false }): void => {
      const opts = { 'elk.direction': direction, ...elkOptions };
      const ns = useInitialNodes ? initialNodes : nodes;
      const es = useInitialNodes ? initialEdges : edges;

      getLayoutedElements(ns, es, opts).then(({ nodes: layoutedNodes, edges: layoutedEdges }) => {
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);

        window.requestAnimationFrame(() => fitView());
      });
    },
    [nodes, edges]
  );

  useLayoutEffect(() => {
    onLayout({ direction: 'DOWN', useInitialNodes: true });
  }, []);

  return (
    <NodeStateProvider.Provider
      value={{
        highlightedActions: props.previousActions,
        hoverAction: props.hoverAction,
        currentAction: props.currentAction
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        edgesUpdatable={false}
        nodesDraggable={false}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
      />
      <MiniMap pannable className="pr-10" />
      <Controls position="bottom-right" />
    </NodeStateProvider.Provider>
  );
};

export const GraphView = (props: {
  stateMachine: ApplicationModel;
  currentAction: Step | undefined;
  highlightedActions: Step[] | undefined;
  hoverAction: Step | undefined;
}) => {
  const parentRef = useRef<HTMLDivElement | null>(null);
  const childRef = useRef<HTMLDivElement | null>(null);

  return (
    <div ref={parentRef} className="h-full w-full flex-1">
      <div ref={childRef} className="h-full w-full">
        <ReactFlowProvider>
          <_Graph
            stateMachine={props.stateMachine}
            currentAction={props.currentAction}
            previousActions={props.highlightedActions}
            hoverAction={props.hoverAction}
          />
        </ReactFlowProvider>
      </div>
    </div>
  );
};
