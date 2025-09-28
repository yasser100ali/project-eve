import { auth } from '@/app/(auth)/auth';
// Mock imports - no DB queries needed
// import { getMessagesByChatId, getStreamIdsByChatId } from '@/lib/db/queries';
import { ChatSDKError } from '@/lib/errors';
import type { ChatMessage } from '@/lib/types';
import { createUIMessageStream, JsonToSseTransformStream } from 'ai';
import { getStreamContext } from '@/lib/stream-context';
import { differenceInSeconds } from 'date-fns';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: streamId } = await params;

  // Mock DB functions - no-DB mode
  const mockChat = {
    id: streamId,
    userId: 'mock-user',
    title: 'Mock Stream Chat',
    visibility: 'private' as const,
    createdAt: new Date(),
  };

  let chat: typeof mockChat;
  try {
    // Skip DB fetch
    // chat = await getChatById({ id: chatId });
    chat = mockChat;
    console.log('Mock getChatById in stream route - mock chat');
  } catch {
    return new ChatSDKError('not_found:chat').toResponse();
  }

  if (!chat) {
    return new ChatSDKError('not_found:chat').toResponse();
  }

  const session = await auth();

  if (!session?.user || session.user.id !== chat.userId) {
    return new ChatSDKError('unauthorized:stream').toResponse();
  }

  const streamContext = getStreamContext();
  const resumeRequestedAt = new Date();

  if (!streamContext) {
    return new Response(null, { status: 204 });
  }

  const chatId = streamId; // Use streamId as chatId for mock
  if (!chatId) {
    return new ChatSDKError('bad_request:api').toResponse();
  }

  if (chat.visibility === 'private' && chat.userId !== session.user.id) {
    return new ChatSDKError('forbidden:chat').toResponse();
  }

  // Mock stream IDs - no DB
  // const streamIds = await getStreamIdsByChatId({ chatId });
  const streamIds = [streamId];
  console.log('Mock getStreamIdsByChatId - mock stream');

  if (!streamIds.length) {
    return new ChatSDKError('not_found:stream').toResponse();
  }

  const recentStreamId = streamIds.at(-1);

  if (!recentStreamId) {
    return new ChatSDKError('not_found:stream').toResponse();
  }

  const emptyDataStream = createUIMessageStream<ChatMessage>({
    execute: () => {},
  });

  const stream = await streamContext.resumableStream(recentStreamId, () =>
    emptyDataStream.pipeThrough(new JsonToSseTransformStream()),
  );

  /*
   * For when the generation is streaming during SSR
   * but the resumable stream has concluded at this point.
   */
  if (!stream) {
    // Mock messages - no DB
    // const messages = await getMessagesByChatId({ id: chatId });
    const messages: any[] = [];
    console.log('Mock getMessagesByChatId in stream - empty');
    const mostRecentMessage = messages.at(-1);

    if (!mostRecentMessage) {
      return new Response(emptyDataStream, { status: 200 });
    }

    if (mostRecentMessage.role !== 'assistant') {
      return new Response(emptyDataStream, { status: 200 });
    }

    const messageCreatedAt = new Date(mostRecentMessage.createdAt);

    if (differenceInSeconds(resumeRequestedAt, messageCreatedAt) > 15) {
      return new Response(emptyDataStream, { status: 200 });
    }

    const restoredStream = createUIMessageStream<ChatMessage>({
      execute: ({ writer }) => {
        writer.write({
          type: 'data-appendMessage',
          data: JSON.stringify(mostRecentMessage),
          transient: true,
        });
      },
    });

    return new Response(
      restoredStream.pipeThrough(new JsonToSseTransformStream()),
      { status: 200 },
    );
  }

  return new Response(stream, { status: 200 });
}
