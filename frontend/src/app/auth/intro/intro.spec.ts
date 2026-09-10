import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import Intro from './intro';

describe('Intro', () => {
  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
  });

  afterEach(() => {
    vi.useRealTimers();
    sessionStorage.clear();
  });

  // Deliberately synchronous: fixture.whenStable() leans on the zoneless
  // scheduler's own setTimeout, so awaiting it under fake timers never resolves.
  function render() {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const fixture = TestBed.createComponent(Intro);
    fixture.detectChanges();
    return { fixture, navigate };
  }

  it('plays the animation on the first visit of a session', () => {
    vi.useFakeTimers();
    const { fixture, navigate } = render();

    expect(fixture.nativeElement.querySelector('.intro.done')).toBeNull();
    expect(navigate).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1600);

    expect(navigate).toHaveBeenCalledWith('/login');
    expect(sessionStorage.getItem('dabubble.intro')).toBe('1');
    fixture.destroy();
  });

  it('skips straight to login once it has been seen', () => {
    sessionStorage.setItem('dabubble.intro', '1');
    const { fixture, navigate } = render();

    expect(fixture.nativeElement.querySelector('.intro.done')).not.toBeNull();
    expect(navigate).toHaveBeenCalledWith('/login');
    fixture.destroy();
  });

  it('still plays when sessionStorage is unavailable', () => {
    // Private-mode browsers throw on access rather than returning null. The
    // splash must not take the bootstrap down with it.
    const getItem = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('SecurityError');
    });
    const setItem = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('SecurityError');
    });

    vi.useFakeTimers();
    const { fixture, navigate } = render();

    expect(fixture.nativeElement.querySelector('.intro.done')).toBeNull();
    vi.advanceTimersByTime(1600);
    expect(navigate).toHaveBeenCalledWith('/login');

    fixture.destroy();
    getItem.mockRestore();
    setItem.mockRestore();
  });

  it('drops its pending timer when it is destroyed', () => {
    vi.useFakeTimers();
    const { fixture, navigate } = render();

    fixture.destroy();
    vi.advanceTimersByTime(1600);

    expect(navigate).not.toHaveBeenCalled();
  });
});
