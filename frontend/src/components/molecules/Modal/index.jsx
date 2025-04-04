import { Modal, ModalVariant } from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import ILabMetadata from "@/components/templates/ILab/ILabMetadata";
import React from "react";
import { setModalOpen } from "@/actions/ilabActions";

const ModalComponent = () => {
  const dispatch = useDispatch();
  const { isModalOpen, metadataItem } = useSelector((state) => state.ilab);
  const handleModalToggle = () => {
    dispatch(setModalOpen());
  };
  return (
    <React.Fragment>
      <Modal
        variant={ModalVariant.large}
        title={"MetaData"}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
      >
        {metadataItem && Object.keys(metadataItem).length > 0 && (
          <ILabMetadata item={metadataItem} />
        )}
      </Modal>
    </React.Fragment>
  );
};

export default ModalComponent;
