import NextAuth from 'next-auth';
import { authConfig } from './auth.config';

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  adapter: undefined, // Disable DB adapter
  providers: [
    // CredentialsProvider({
    //   // ... existing credentials config if present
    // }),
    // Comment out or remove guest provider
    // GuestProvider({
    //   id: 'guest',
    //   name: 'Guest',
    //   type: 'credentials',
    //   authorize: async () => ({ id: 'guest' }),
    //   // ... rest
    // }),
  ],
  session: {
    strategy: 'jwt', // Use JWT, no DB sessions
  },
  callbacks: {
    // ... existing callbacks, ensure no DB calls
  },
  // ... rest of config, no DB adapter
});

export const runtime = 'nodejs';
