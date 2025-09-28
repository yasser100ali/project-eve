import { auth } from '@/app/(auth)/auth';
import type { NextRequest } from 'next/server';
import { getChatsByUserId } from '@/lib/db/queries';
import { ChatSDKError } from '@/lib/errors';

export async function GET(request: Request) {
  const session = await auth();

  if (!session?.user) {
    return new ChatSDKError('unauthorized:chat').toResponse();
  }

  // Mock empty history - no DB
  // const chats = await getChatsByUserId({ userId: session.user.id });
  const chats = [];
  console.log('Skipped getChatsByUserId - no DB, returning empty');

  return Response.json(chats);
}
