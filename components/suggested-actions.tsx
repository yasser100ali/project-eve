'use client';

import { motion } from 'framer-motion';
import { memo } from 'react';
import type { UseChatHelpers } from '@ai-sdk/react';
import type { VisibilityType } from './visibility-selector';
import type { ChatMessage } from '@/lib/types';
import { Suggestion } from './elements/suggestion';

interface SuggestedActionsProps {
  chatId: string;
  sendMessage: UseChatHelpers<ChatMessage>['sendMessage'];
  selectedVisibilityType: VisibilityType;
}

function PureSuggestedActions({
  chatId,
  sendMessage,
  selectedVisibilityType,
}: SuggestedActionsProps) {
  const suggestedActions = [
    'What are some ideas to further make an AI Lawyer?',
    'How could I use this chatbot?',
    'Why hire Yasser?',
    'How could we reduce hallucinations in AI Agents?',
  ];

  return (
    <div
      data-testid="suggested-actions"
      className="grid sm:grid-cols-2 gap-2 w-full"
    >
      {suggestedActions.map((suggestedAction, index) => (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ delay: 0.05 * index }}
          key={suggestedAction}
        >
          <Suggestion
            suggestion={suggestedAction}
            onClick={(suggestion) => {
              window.history.replaceState({}, '', `/chat/${chatId}`);
              sendMessage({
                role: 'user',
                parts: [{ type: 'text', text: suggestion }],
              });
            }}
            className="text-left w-full h-auto whitespace-normal p-3"
          >
            {suggestedAction}
          </Suggestion>
        </motion.div>
      ))}
    </div>
  );
}

export const SuggestedActions = memo(
  PureSuggestedActions,
  (prevProps, nextProps) => {
    if (prevProps.chatId !== nextProps.chatId) return false;
    if (prevProps.selectedVisibilityType !== nextProps.selectedVisibilityType)
      return false;

    return true;
  },
);
