import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { User } from '../../../core/auth/user';
import { Avatar } from './avatar';

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

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Avatar],
  template: '<app-avatar [user]="user()" [showPresence]="showPresence()" />',
})
class Host {
  readonly user = signal<User | null>(makeUser());
  readonly showPresence = signal(true);
}

describe('Avatar', () => {
  async function render() {
    const fixture = TestBed.createComponent(Host);
    await fixture.whenStable();
    return fixture;
  }

  it('uses the uploaded avatar when there is one', async () => {
    const fixture = await render();
    fixture.componentInstance.user.set(makeUser({ avatar: '/media/avatars/ada.png' }));
    await fixture.whenStable();

    const img = fixture.nativeElement.querySelector('img') as HTMLImageElement;
    expect(img.getAttribute('src')).toBe('/media/avatars/ada.png');
  });

  it('maps a default slug to its asset', async () => {
    const fixture = await render();
    fixture.componentInstance.user.set(makeUser({ default_avatar: 'quiff' }));
    await fixture.whenStable();

    const img = fixture.nativeElement.querySelector('img') as HTMLImageElement;
    expect(img.getAttribute('src')).toBe('/avatars/quiff.svg');
  });

  it('names the person in the alt text', async () => {
    const fixture = await render();
    const img = fixture.nativeElement.querySelector('img') as HTMLImageElement;
    expect(img.alt).toBe('Profilbild von Ada Lovelace');
  });

  it('shows the presence dot only when the user is online', async () => {
    const fixture = await render();
    expect(fixture.nativeElement.querySelector('[data-testid="presence"]')).toBeNull();

    fixture.componentInstance.user.set(makeUser({ is_online: true }));
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('[data-testid="presence"]')).not.toBeNull();
  });

  it('can suppress the presence dot', async () => {
    const fixture = await render();
    fixture.componentInstance.user.set(makeUser({ is_online: true }));
    fixture.componentInstance.showPresence.set(false);
    await fixture.whenStable();

    expect(fixture.nativeElement.querySelector('[data-testid="presence"]')).toBeNull();
  });
});
