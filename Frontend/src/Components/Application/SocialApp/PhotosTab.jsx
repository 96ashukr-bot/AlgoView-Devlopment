import React, { Fragment, useState, useEffect } from "react";
import { Col, Row, Card, CardBody } from "reactstrap";
import Lightbox from "react-18-image-lightbox";
import axios from "axios";
import { PortfolioTitle } from "../../../Constant";
import { BigImageApi, ImageLightApi } from "../../../api";
import { H4, Image, P } from "../../../AbstractElements";

const PhotosTab = () => {
  const description = "is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy.";
  const [images, setImage] = useState([]);
  const [smallImages, setsmallImages] = useState([]);

  const initilindex = { index: 0, isOpen: false };
  const [photoIndex, setPhotoIndex] = useState(initilindex);

  const onMovePrev = () => {
    const prev = (photoIndex.index + images.length - 1) % images.length;
    setPhotoIndex({ ...photoIndex, index: prev });
  };

  const onMoveNext = () => {
    const next = (photoIndex.index + 1) % images.length;
    setPhotoIndex({ ...photoIndex, index: next });
  };

  useEffect(() => {
    axios.get(ImageLightApi).then((response) => {
      setImage(response.data.src);
    });

    axios.get(BigImageApi).then((response) => {
      setsmallImages(response.data.src);
    });
  }, []);

  return (
    <Fragment>
      <Row>
        {smallImages ? (
          <Col sm="12">
            <Card>
              <CardBody>
                <div className="my-gallery row gallery-with-description">
                  {smallImages
                    ? smallImages.map((item, i) => {
                        return (
                          <figure className="col-xl-3 col-sm-6" key={i}>
                            <a href="#javascript" data-size="1600x950">
                              <Image
                                attrImage={{
                                  src: require(`../../../assets/images/${item}`),
                                  alt: "Gallery",
                                  className: "img-thumbnail",
                                  onClick: () => setPhotoIndex({ ...photoIndex, index: 1, isOpen: true }),
                                }}
                              />
                              <div className="caption">
                                <H4>{PortfolioTitle}</H4>
                                <P>{description}</P>
                              </div>
                            </a>
                          </figure>
                        );
                      })
                    : ""}
                </div>
              </CardBody>
            </Card>
          </Col>
        ) : (
          ""
        )}
      </Row>
      {photoIndex.isOpen && (
        <Lightbox mainSrc={require(`../../../assets/images/${images[photoIndex.index]}`)} nextSrc={require(`../../../assets/images/${images[(photoIndex.index + 1) % images.length]}`)} prevSrc={require(`../../../assets/images/${images[(photoIndex.index + images.length - 1) % images.length]}`)} imageTitle={photoIndex.index + 1 + "/" + images.length} onCloseRequest={() => setPhotoIndex({ ...photoIndex, isOpen: false })} onMovePrevRequest={onMovePrev} onMoveNextRequest={onMoveNext} />
      )}
    </Fragment>
  );
};

export default PhotosTab;
