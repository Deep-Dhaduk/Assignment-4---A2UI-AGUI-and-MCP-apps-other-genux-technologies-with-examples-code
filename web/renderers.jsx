import React, { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { defineCatalog } from "@json-render/core";
import { schema } from "@json-render/react/schema";
import {
  defineRegistry,
  Renderer as JsonRenderer,
  JSONUIProvider,
} from "@json-render/react";
import {
  defineComponent,
  createLibrary,
  Renderer as OpenRenderer,
} from "@openuidev/react-lang";
import { MessageProcessor } from "@a2ui/web_core/v0_9";
import { injectBasicCatalogStyles } from "@a2ui/web_core/v0_9/basic_catalog";
import { A2uiSurface, basicCatalog, Context } from "@a2ui/lit/v0_9";
import { ContextProvider } from "@lit/context";
import { renderMarkdown } from "@a2ui/markdown-it";
import { Panel, Stat, Note, Agenda, Action, Sandbox } from "./components.jsx";

export const propSchemas = {
  Panel: z.object({ title: z.string() }),
  Stat: z.object({ label: z.string(), value: z.string() }),
  Note: z.object({ text: z.string() }),
  Agenda: z.object({ items: z.array(z.string()) }),
  Action: z.object({ label: z.string(), action: z.literal("add_attendees") }),
  Sandbox: z.object({ html: z.string() }),
};
const definitions = { Panel, Stat, Note, Agenda, Action, Sandbox };
export const catalog = defineCatalog(schema, {
  components: Object.fromEntries(
    Object.entries(propSchemas).map(([name, props]) => [
      name,
      {
        props,
        description: `Campus ${name} component`,
        ...(name === "Panel" ? { slots: ["default"] } : {}),
      },
    ]),
  ),
  actions: {},
});
const { registry } = defineRegistry(catalog, {
  components: Object.fromEntries(
    Object.entries(definitions).map(([name, Component]) => [
      name,
      ({ props, children }) => <Component {...props}>{children}</Component>,
    ]),
  ),
});
export function JsonView({ spec }) {
  return (
    <JSONUIProvider registry={registry}>
      <JsonRenderer spec={spec} registry={registry} />
    </JSONUIProvider>
  );
}

const leaves = Object.entries(definitions)
  .filter(([name]) => name !== "Panel")
  .map(([name, Component]) =>
    defineComponent({
      name,
      description: `Campus ${name}`,
      props: propSchemas[name],
      component: ({ props }) => <Component {...props} />,
    }),
  );
const OpenPanel = defineComponent({
  name: "Panel",
  description: "Event panel with a title and a list of leaf components",
  props: z.object({
    title: z.string(),
    children: z.array(z.union(leaves.map((c) => c.ref))),
  }),
  component: ({ props, renderNode }) => (
    <Panel title={props.title}>{renderNode(props.children)}</Panel>
  ),
});
export const library = createLibrary({
  root: "Panel",
  components: [OpenPanel, ...leaves],
});
export function OpenView({ program, streaming = false }) {
  const [errors, setErrors] = useState([]);
  return (
    <>
      <OpenRenderer
        library={library}
        response={program}
        isStreaming={streaming}
        onError={(e) => setErrors(e)}
      />
      {errors.length > 0 && (
        <p className="error" role="alert">
          {errors.map((e) => e.message).join("; ")}
        </p>
      )}
    </>
  );
}

export function A2uiView({ messages }) {
  const container = useRef(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const host = container.current;
    host.replaceChildren();
    setError("");
    const provider = new ContextProvider(host, {
      context: Context.markdown,
      initialValue: renderMarkdown,
    });
    const processor = new MessageProcessor([basicCatalog]);
    injectBasicCatalogStyles();
    processor.onSurfaceCreated((surface) => {
      const element = new A2uiSurface();
      element.surface = surface;
      host.append(element);
    });
    processor.onSurfaceDeleted(() => host.replaceChildren());
    try {
      processor.processMessages(messages);
    } catch (e) {
      setError(e.message);
    }
    return () => {
      host.replaceChildren();
      provider.hostDisconnected?.();
    };
  }, [messages]);
  return (
    <>
      <div className="a2ui-surface" ref={container} />
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </>
  );
}
