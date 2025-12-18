<script lang="ts">
  import { marked } from "marked";
  import { scale, slide } from "svelte/transition";

  let messages = $state<{ text: string; isUser: boolean }[]>([]);
  let input = $state("");
  let files = $state<FileList | null>(null);
  let fileInput: HTMLInputElement;

  const socket = new WebSocket("ws://localhost:8000/ws");

  socket.addEventListener("message", (e) => {
    messages.push({ text: e.data, isUser: false });
  });

  const readFile = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const handleSend = async () => {
    let messageToSend = input;
    let displayMessage = input;

    if (files && files.length > 0) {
      const file = files[0];
      const content = await readFile(file);
      const userRequest =
        input.trim().length === 0 ? "Please analyze this file." : input;
      messageToSend = `I have uploaded a file named "${file.name}" with the following content:\n\n${content}\n\nUser Request: ${userRequest}`;
      displayMessage += `\n\n*[Attached file: ${file.name}]*`;
    }

    if (messageToSend.trim().length === 0) return;

    socket.send(messageToSend);
    messages.push({ text: displayMessage, isUser: true });

    input = "";
    if (fileInput) {
      fileInput.value = "";
      files = null;
    }
  };
</script>

<div
  class="h-dvh aspect-square mx-auto flex flex-col items-center max-w-full p-4 gap-2"
>
  <div
    class="flex-1 overflow-y-auto h-full w-full [scrollbar-width:none] relative"
  >
    {#if messages.length === 0}
      <div
        class="absolute inset-0 flex flex-col h-full justify-center items-center text-3xl gap-2 pointer-events-none"
        transition:scale
      >
        <img src="cry.webp" class="size-16" alt="cry face emoji" />
        <h1 class="font-extrabold">Тут пока что пусто :(</h1>
      </div>
    {/if}
    {#each messages as message (message)}
      <div transition:slide={{ axis: "y" }}>
        <div class="chat {message.isUser ? 'chat-end' : 'chat-start'}">
          <div class="bg-base-300 max-w-11/12 p-4 shadow-lg rounded-3xl">
            {@html marked.parse(message.text) as string}
          </div>
        </div>
      </div>
    {/each}
  </div>
  <div class="w-full relative">
    <textarea
      bind:value={input}
      class="textarea [scrollbar-width:none] textarea-bordered w-full rounded-3xl shadow-lg h-24 text-xl pt-4 pr-24 resize-none bg-base-100"
      placeholder="Спросите меня о чём нибудь"
    ></textarea>
    <input type="file" bind:files bind:this={fileInput} class="hidden" />
    <button
      class="btn btn-circle absolute left-2 bottom-2 {files && files.length > 0
        ? 'text-accent'
        : 'text-base-content/50'}"
      onclick={() => fileInput?.click()}
      aria-label="attach file"
    >
      <svg
        class="fill-current"
        height="24px"
        viewBox="0 -960 960 960"
        width="24px"
        ><path
          d="M440-320v-326L336-542l-56-58 200-200 200 200-56 58-104-104v326h-80ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"
        /></svg
      >
    </button>
    <button
      onclick={handleSend}
      disabled={input.length === 0 ||
        ((!files || files.length === 0) && input.length === 0)}
      class="btn h-20 w-20 rounded-3xl btn-accent p-2 absolute right-2 top-2"
      aria-label="send text"
    >
      <svg class="p-3" viewBox="0 -960 960 960" fill="currentColor"
        ><path
          d="M120-160v-640l760 320-760 320Zm80-120 474-200-474-200v140l240 60-240 60v140Zm0 0v-400 400Z"
        /></svg
      >
    </button>
  </div>
</div>
