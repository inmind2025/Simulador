import { IDeferred } from './types';
export declare function getId(): string;
export declare function noop(): void;
export declare function walkTree<T extends {
    children?: T[];
}, U = void>(tree: T, callback: (item: T, next: () => U[] | undefined, parent?: T) => U): U;
export declare function addClass(className: string, ...rest: string[]): string;
export declare function wrapFunction<T extends unknown[], U>(fn: (...args: T) => U, wrapper: (fn: (...args: T) => U, ...args: T) => U): (...args: T) => U;
export declare function defer<T = void>(): IDeferred<T>;
export declare function memoize<T extends unknown[], U>(fn: (...args: T) => U): (...args: T) => U;
export declare function debounce<T extends unknown[], U>(fn: (...args: T) => U, time: number): (...args: T) => U | undefined;
