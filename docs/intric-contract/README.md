# How Intric connects to your server

A server can pass every local test and still not work in Intric. These are the Intric-side behaviors that cause that.

## The server URL

Enter the URL exactly as `https://<your-host>/mcp`, with no trailing slash. Intric stores the URL as you typed it. With a trailing slash the server answers with a redirect, and the MCP session ends with `Session terminated`.

## Intric keeps its own copy of your tool list

Intric reads your tool list (names, parameters, docstrings) when you add the server, and keeps that copy. It does not read the list again on its own. After you add, remove or rename a tool, or change its parameters or docstring, open the server in Intric and click **Refresh capabilities**. Until then, assistants keep using the stored list, even though your server has the new one.

If a refresh shows no error but the tool list does not change, check your server log at the time of the refresh. Intric calls `tools/list` with the Api Key it has stored. If your server rejects that key with `401`, for example after you changed the secret, issuer or audience in `.env`, Intric keeps showing the old list and reports no error. Generate a new token, update the Api Key on the server in Intric, then refresh again.

## Adding the server and turning it on are separate steps

When you add the server, Intric creates the connection and reads your tools. Assistants still cannot use the server until a tenant admin turns it on for the tenant and gives it a security classification. This is one setting for the whole server, not one per tool. If either step is missing, the server does not appear where assistants pick their tools. This holds even when the server is registered and its tool list is up to date.

## Checklist

- The URL ends in `/mcp`, with no trailing slash.
- After you add or remove a tool, or change a tool's name, parameters or docstring, click **Refresh capabilities**. Then check that Intric shows the new list.
- A tenant admin has turned the server on and set its security classification.
