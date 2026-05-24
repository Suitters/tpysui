from __future__ import annotations

from typing import Any, Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Checkbox, Input, Label, Select

from ..services.base import AddressInfo, ObjectSummaryInfo
from ..utils.validators import valid_sui_address

_OTHER = "__other__"


class PlainInput(Widget):
    """Single text input with optional validator. Used for most scalar args."""

    def __init__(
        self,
        label: str,
        validator: Callable[[str], bool] | None = None,
        optional: bool = False,
        default: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._arg_name = label
        self._validator = validator
        self._optional = optional
        self._default = default

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"{self._arg_name}:")
            yield Input(value=self._default, id="inp", placeholder="" if not self._optional else "(optional)")

    def get_name_value(self) -> tuple[str, Any]:
        v = self.query_one(Input).value.strip()
        if not v:
            return self._arg_name, None
        return self._arg_name, v

    def validate(self) -> str | None:
        v = self.query_one(Input).value.strip()
        if not v:
            if self._optional:
                return None
            return f"{self._arg_name}: required"
        if self._validator and not self._validator(v):
            return f"{self._arg_name}: invalid format"
        return None


class MultiValueInput(Widget):
    """Comma-separated multi-value input. Produces list[str]."""

    def __init__(
        self,
        label: str,
        validator: Callable[[str], bool] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._arg_name = label
        self._validator = validator

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"{self._arg_name}:")
            yield Input(id="inp", placeholder="comma-separated values")

    def get_name_value(self) -> tuple[str, Any]:
        raw = self.query_one(Input).value
        items = [x.strip() for x in raw.split(",") if x.strip()]
        return self._arg_name, items if items else None

    def validate(self) -> str | None:
        raw = self.query_one(Input).value
        items = [x.strip() for x in raw.split(",") if x.strip()]
        if not items:
            return f"{self._arg_name}: at least one value required"
        if self._validator:
            for item in items:
                if not self._validator(item):
                    return f"{self._arg_name}: '{item[:12]}…' invalid format"
        return None


class AddressSelect(Widget):
    """Select from active group addresses or enter manually."""

    def __init__(self, label: str, addresses: list[AddressInfo], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._arg_name = label
        self._addresses = addresses

    def compose(self) -> ComposeResult:
        options: list[tuple[str, str]] = [
            (f"{a.alias} ({a.address[:8]}…)", a.address) for a in self._addresses
        ]
        options.append(("Other…", _OTHER))
        with Horizontal():
            yield Label(f"{self._arg_name}:")
            yield Select(options, id="sel", allow_blank=False)
            yield Input(id="other_inp", placeholder="0x…")

    def on_mount(self) -> None:
        self.query_one("#other_inp", Input).display = False
        if self._addresses:
            self.query_one(Select).value = self._addresses[0].address

    def on_select_changed(self, event: Select.Changed) -> None:
        self.query_one("#other_inp", Input).display = (event.value == _OTHER)

    def get_name_value(self) -> tuple[str, Any]:
        sel = self.query_one(Select)
        if sel.value == _OTHER:
            return self._arg_name, self.query_one("#other_inp", Input).value.strip() or None
        return self._arg_name, sel.value if sel.value is not Select.BLANK else None

    def validate(self) -> str | None:
        sel = self.query_one(Select)
        if sel.value == _OTHER:
            v = self.query_one("#other_inp", Input).value.strip()
            if not v:
                return f"{self._arg_name}: required"
            if not valid_sui_address(v):
                return f"{self._arg_name}: invalid Sui address"
        elif sel.value is Select.BLANK:
            return f"{self._arg_name}: required"
        return None


class ObjectSelect(Widget):
    """Select from owned objects (eager-loaded) or enter manually."""

    def __init__(self, label: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._arg_name = label

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"{self._arg_name}:")
            yield Select([("Loading…", "__loading__")], id="sel", allow_blank=False)
            yield Input(id="other_inp", placeholder="0x…")

    def on_mount(self) -> None:
        self.query_one("#other_inp", Input).display = False

    def populate(self, objects: list[ObjectSummaryInfo]) -> None:
        options: list[tuple[str, str]] = [
            (f"{o.object_id[:10]}… — {o.object_type[:24]}", o.object_id)
            for o in objects
        ]
        options.append(("Other…", _OTHER))
        sel = self.query_one(Select)
        sel.set_options(options)

    def on_select_changed(self, event: Select.Changed) -> None:
        self.query_one("#other_inp", Input).display = (event.value == _OTHER)

    def get_name_value(self) -> tuple[str, Any]:
        sel = self.query_one(Select)
        if sel.value == _OTHER:
            return self._arg_name, self.query_one("#other_inp", Input).value.strip() or None
        if sel.value in (Select.BLANK, "__loading__"):
            return self._arg_name, None
        return self._arg_name, sel.value

    def validate(self) -> str | None:
        sel = self.query_one(Select)
        if sel.value == _OTHER:
            v = self.query_one("#other_inp", Input).value.strip()
            if not v:
                return f"{self._arg_name}: required"
            if not valid_sui_address(v):
                return f"{self._arg_name}: invalid Sui address"
        elif sel.value in (Select.BLANK, "__loading__"):
            return f"{self._arg_name}: required"
        return None


class ObjectChecklist(Widget):
    """Checklist accumulator for object_ids. Multi-select + manual entry."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._arg_name = "object_ids"
        self._objects: list[ObjectSummaryInfo] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("object_ids:")
            yield Vertical(id="checklist")
            with Horizontal():
                yield Label("Other:")
                yield Input(id="other_inp", placeholder="0x… (comma-separated)")

    def populate(self, objects: list[ObjectSummaryInfo]) -> None:
        self._objects = objects
        checklist = self.query_one("#checklist")
        checklist.remove_children()
        for obj in objects:
            label = f"{obj.object_id[:10]}… — {obj.object_type[:24]}"
            checklist.mount(Checkbox(label, id=f"chk_{obj.object_id[:16]}"))

    def get_name_value(self) -> tuple[str, Any]:
        checked = [
            obj.object_id
            for obj, chk in zip(
                self._objects,
                self.query_one("#checklist").query(Checkbox),
            )
            if chk.value
        ]
        manual_raw = self.query_one("#other_inp", Input).value
        manual = [x.strip() for x in manual_raw.split(",") if x.strip()]
        combined = checked + manual
        return self._arg_name, combined if combined else None

    def validate(self) -> str | None:
        _, value = self.get_name_value()
        if not value:
            return "object_ids: at least one object required"
        manual_raw = self.query_one("#other_inp", Input).value
        manual = [x.strip() for x in manual_raw.split(",") if x.strip()]
        for item in manual:
            if not valid_sui_address(item):
                return f"object_ids: '{item[:12]}…' invalid address"
        return None


class ForVersionsWidget(Widget):
    """Object picker + multi-version input for GetMultiplePastObjects."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._arg_name = "for_versions"
        self._object_id: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield Label("object_id:")
                yield Select([("Loading…", "__loading__")], id="obj_sel", allow_blank=False)
                yield Input(id="other_inp", placeholder="0x…")
            with Horizontal():
                yield Label("versions:")
                yield Input(id="versions_inp", placeholder="comma-separated unsigned ints")

    def on_mount(self) -> None:
        self.query_one("#other_inp", Input).display = False

    def populate(self, objects: list[ObjectSummaryInfo]) -> None:
        options: list[tuple[str, str]] = [
            (f"{o.object_id[:10]}… — {o.object_type[:24]}", o.object_id)
            for o in objects
        ]
        options.append(("Other…", _OTHER))
        self.query_one("#obj_sel", Select).set_options(options)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "obj_sel":
            self.query_one("#other_inp", Input).display = (event.value == _OTHER)

    def _get_object_id(self) -> str | None:
        sel = self.query_one("#obj_sel", Select)
        if sel.value == _OTHER:
            return self.query_one("#other_inp", Input).value.strip() or None
        if sel.value in (Select.BLANK, "__loading__"):
            return None
        return str(sel.value)

    def get_name_value(self) -> tuple[str, Any]:
        obj_id = self._get_object_id()
        if not obj_id:
            return self._arg_name, None
        raw = self.query_one("#versions_inp", Input).value
        try:
            versions = [int(v.strip()) for v in raw.split(",") if v.strip()]
        except ValueError:
            return self._arg_name, None
        if not versions:
            return self._arg_name, None
        return self._arg_name, [{"objectId": obj_id, "version": v} for v in versions]

    def validate(self) -> str | None:
        obj_id = self._get_object_id()
        sel = self.query_one("#obj_sel", Select)
        if sel.value == _OTHER:
            if not obj_id:
                return "for_versions: object_id required"
            if not valid_sui_address(obj_id):
                return "for_versions: invalid Sui address"
        elif not obj_id:
            return "for_versions: object required"
        raw = self.query_one("#versions_inp", Input).value
        parts = [v.strip() for v in raw.split(",") if v.strip()]
        if not parts:
            return "for_versions: at least one version required"
        for p in parts:
            if not p.isdigit():
                return f"for_versions: '{p}' is not an unsigned int"
        return None
