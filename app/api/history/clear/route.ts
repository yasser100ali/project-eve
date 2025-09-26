import { auth } from '@/app/(auth)/auth';
import { deleteAllChatsByUserId } from '@/lib/db/queries';
import { ChatSDKError } from '@/lib/errors';

export async function DELETE(request: Request) {
  try {
    const session = await auth();

    if (!session?.user) {
      return new ChatSDKError('unauthorized:chat').toResponse();
    }

    await deleteAllChatsByUserId({ userId: session.user.id });

    return Response.json({ success: true }, { status: 200 });
  } catch (error) {
    if (error instanceof ChatSDKError) {
      return error.toResponse();
    }

    console.error('Unhandled error in clear history API:', error);
    return new ChatSDKError('offline:chat').toResponse();
  }
}
