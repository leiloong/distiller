"""
This file runs the main training/val loop, etc... using Lightning Trainer    
"""
from pytorch_lightning import Trainer
from argparse import ArgumentParser
from research_seed.baselines.rkd_baseline.rkd_distiller_trainer import RKD_Cifar
from pytorch_lightning.logging import TestTubeLogger
from research_seed.baselines.rkd_baseline.rkd_distiller_trainer import load_model_chk, Train_Mode, addEmbedding
from research_seed.baselines.model.model_factory import create_cnn_model, is_resnet

def main(hparams):
    # init module
    teacher_base = create_cnn_model(hparams.teacher_model, feature_maps=True, dataset=hparams.dataset)
    teacher = addEmbedding(teacher_base, hparams)

    student_base = create_cnn_model(hparams.student_model, feature_maps=True, dataset=hparams.dataset)
    student = addEmbedding(student_base, hparams)

    # Loading from checkpoint
    teacher = load_model_chk(teacher, hparams.path_to_teacher)

    # Train Teacher Embedding
    model = RKD_Cifar(student_base=student, teacher_base=teacher, mode=Train_Mode.STUDENT, hparams=hparams)

    logger = TestTubeLogger(
       save_dir=hparams.save_dir,
       version=hparams.version # An existing version with a saved checkpoint
    )

    # most basic trainer, uses good defaults
    if hparams.gpus > 1:
      dist = 'ddp'
    else:
      dist = None

    # most basic trainer, uses good defaults
    trainer = Trainer(
        max_nb_epochs=hparams.epochs,
        gpus=hparams.gpus,
        nb_gpu_nodes=hparams.nodes,
        early_stop_callback=None,
        logger=logger,
        default_save_path=hparams.save_dir,
        distributed_backend=dist,
    )

    trainer.fit(model)


if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--epochs', default=100, type=int,  help='number of total epochs to run')
    parser.add_argument('--gpus', type=int, default=1)
    parser.add_argument('--nodes', type=int, default=1)
    parser.add_argument('--save-dir', type=str, default='./lightning_logs')
    parser.add_argument('--version', type=int, required=True, help= "version number for experiment")
    # give the module a chance to add own params
    # good practice to define LightningModule speficic params in the module
    parser = RKD_Cifar.add_model_specific_args(parser)

    # parse params
    hparams = parser.parse_args()

    main(hparams)
