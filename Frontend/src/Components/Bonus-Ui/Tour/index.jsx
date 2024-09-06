import React, { Fragment } from "react";
import { disableBodyScroll, enableBodyScroll } from "body-scroll-lock";
import { TourProvider, useTour } from "@reactour/tour";
import TourMain from "./MainTour";

const steps = [
  {
    selector: ".step1",
    content: "This is Profile image",
  },
  {
    selector: ".step2",
    content: "Change Profile image here",
  },
  {
    selector: ".step3",
    content: "This is the your details",
  },
  {
    selector: ".step4",
    content: "This is your Social details",
  },
  {
    selector: ".step5",
    content: "This is the your first Post",
  },
];

const Tours = () => {
  const { setIsOpen } = useTour();
  const disableBody = (target) => disableBodyScroll(target);
  const enableBody = (target) => enableBodyScroll(target);
  return (
    <Fragment>
      <TourProvider steps={steps} isOpen={() => setIsOpen(true)} showPrevNextButtons={true} showCloseButton={true} afterOpen={disableBody} beforeClose={enableBody}>
        <TourMain />
      </TourProvider>
    </Fragment>
  );
};

export default Tours;
