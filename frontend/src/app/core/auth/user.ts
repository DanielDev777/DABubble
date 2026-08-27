/** Mirrors accounts.api.serializers.UserSerializer on the backend. */
export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar: string | null;
  avatar_url: string | null;
  default_avatar: string | null;
  is_guest: boolean;
  is_online: boolean;
}

export const FALLBACK_AVATAR = '/avatars/placeholder.svg';

/**
 * The three avatar fields are mutually exclusive by backend rule — setting one
 * nulls the others — so resolve them in one place instead of branching at every
 * call site.
 */
export function avatarSrc(user: User | null): string {
  if (!user) return FALLBACK_AVATAR;
  if (user.avatar) return user.avatar;
  if (user.avatar_url) return user.avatar_url;
  if (user.default_avatar) return `/avatars/${user.default_avatar}.svg`;
  return FALLBACK_AVATAR;
}
