import { avatarSrc, FALLBACK_AVATAR, User } from './user';

function makeUser(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    email: 'ada@example.com',
    full_name: 'Ada Lovelace',
    avatar: null,
    avatar_url: null,
    default_avatar: null,
    is_guest: false,
    is_online: false,
    ...overrides,
  };
}

describe('avatarSrc', () => {
  it('prefers an uploaded avatar', () => {
    const user = makeUser({ avatar: '/media/avatars/ada.png', avatar_url: 'https://g/x.png' });
    expect(avatarSrc(user)).toBe('/media/avatars/ada.png');
  });

  it('falls back to a remote avatar url', () => {
    expect(avatarSrc(makeUser({ avatar_url: 'https://g/x.png' }))).toBe('https://g/x.png');
  });

  it('maps a default avatar slug to a local asset', () => {
    expect(avatarSrc(makeUser({ default_avatar: 'bald-beard' }))).toBe('/avatars/bald-beard.png');
  });

  it('falls back when nothing is set', () => {
    expect(avatarSrc(makeUser())).toBe(FALLBACK_AVATAR);
    expect(avatarSrc(null)).toBe(FALLBACK_AVATAR);
  });
});
