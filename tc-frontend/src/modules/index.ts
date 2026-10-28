import { BaseProcessor, registry } from "./registry";
import BaseViewer from "./base/BaseViewer.svelte";
import BaseEditor from "./base/BaseEditor.svelte";
import BaseTypeViewer from "./base/BaseTypeViewer.svelte";
import TabularViewer from "./tabular/TabularViewer.svelte";
import TabularEditor from "./tabular/TabularEditor.svelte";
import TabularTypeViewer from "./tabular/TabularTypeViewer.svelte";
import FormulaViewer from "./formula/FormulaViewer.svelte";
import FormulaEditor from "./formula/FormulaEditor.svelte";
import FormulaTypeViewer from "./formula/FormulaTypeViewer.svelte";
import ImageViewer from "./image/ImageViewer.svelte";
import ImageEditor from "./image/ImageEditor.svelte";
import ImageTypeViewer from "./image/ImageTypeViewer.svelte";
import SourceItemViewer from "./source/SourceItemViewer.svelte";

/** Register the built-in content-type renderers. */
export function registerProcessors(): void {
    registry.register(
        new BaseProcessor("Base.v00", "Base Item", BaseViewer, BaseEditor, BaseTypeViewer),
    );
    registry.register(
        new BaseProcessor(
            "SourceItem.v00",
            "Source Item",
            SourceItemViewer,
            null,
            BaseTypeViewer,
        ),
    );
    registry.register(
        new BaseProcessor("Tabular.v00", "Tabular Data", TabularViewer, TabularEditor, TabularTypeViewer),
    );
    registry.register(
        new BaseProcessor("Formula.v00", "Formula Model", FormulaViewer, FormulaEditor, FormulaTypeViewer),
    );
    registry.register(
        new BaseProcessor("Image.v00", "Image Gallery", ImageViewer, ImageEditor, ImageTypeViewer),
    );
    for (const [type, name] of [
        ["dac_web.project", "DAC Web Project"],
        ["tpl.plan", "TPL Plan"],
        ["tpl.log", "TPL Execution Log"],
    ] as const) {
        registry.register(
            new BaseProcessor(type, name, null, null, BaseTypeViewer, false),
        );
    }
}

registerProcessors();

export { registry, BaseProcessor } from "./registry";
export type { ViewerProps, EditorProps, EditorExports, TypeViewerProps } from "./registry";
