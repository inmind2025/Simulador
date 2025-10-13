import { CSSItem, CSSStylesheetItem, IAssets, JSItem, JSScriptItem } from './types';
export declare function loadJS(items: JSItem[], context?: object): Promise<void>;
export declare function loadCSS(items: CSSItem[]): Promise<void>;
export declare function buildJSItem(path: string): JSScriptItem;
export declare function buildCSSItem(path: string): CSSStylesheetItem;
export declare function extractAssets(assets: IAssets): string[];
export declare function mergeAssets(...args: (IAssets | null | undefined)[]): IAssets;
