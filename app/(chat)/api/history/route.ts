import { auth } from '@/app/(auth)/auth';
import type { NextRequest } from 'next/server';
import { getChatsByUserId } from '@/lib/db/queries';
import { ChatSDKError } from '@/lib/errors';

export async function GET(request: Request) {
  const session = await auth();

  if (!session?.user) {
    return new ChatSDKError('unauthorized:chat').toResponse();
  }

  // Mock empty history - no DB, return paginated format
  // const chats = await getChatsByUserId({ userId: session.user.id });
  const chats = { chats: [], hasMore: false };
  console.log('Mock getChatsByUserId - empty paginated response');

  return Response.json(chats);
}
