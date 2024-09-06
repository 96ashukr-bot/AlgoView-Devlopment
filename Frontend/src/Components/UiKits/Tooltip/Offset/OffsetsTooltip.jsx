import React, { Fragment, useState } from "react";
import { Btn, ToolTip } from "../../../../AbstractElements";

const OffsetTooltip = ({ item }) => {
  const [tooltip, setTooltip] = useState(false);
  const toggle = () => setTooltip(!tooltip);
  return (
    <Fragment>
      <Btn attrBtn={{ color: "primary", id: "Tooltip-" + item.id, onClick: toggle }}>{item.btntext}</Btn>
      <ToolTip
        attrToolTip={{
          placement: item.placement,
          isOpen: tooltip,
          target: "Tooltip-" + item.id,
          toggle: toggle,
          offset: item.offset,
        }}>
        {item.tooltip}
      </ToolTip>
    </Fragment>
  );
};

export default OffsetTooltip;
