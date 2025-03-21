import ray
import torch
import quickreduce as qr

class Demo:
    def __init__(self, world_size, rank):
        self.world_size = world_size
        self.rank = rank
        qr.init(world_size, rank)

    def get_comm_handle(self):
        return qr.get_comm_handle()

    def set_comm_handles(self, comm_handles):
        qr.set_comm_handles(comm_handles)

    def allreduce_demo(self):
        # AllReduce with profile=FP16
        # 1=FP16, 2=FP8, 3=Q8, 4=Q6, 5=Q4
        tensor = torch.ones(1024, dtype=torch.float16).cuda()
        result = qr.allreduce(1, tensor)
        assert torch.all(result == self.world_size)
        print(f"Demo {self.rank} got result {result}")

# Create 4 demo layers across 4 GPUs.
N = 4
ray.init(num_gpus=N)
demo = [ray.remote(num_gpus=1)(Demo).remote(N, i) for i in range(N)]

# Share IPC communication handles between the instances.
comm_handles = ray.get([demo[i].get_comm_handle.remote() for i in range(N)])
ray.get([demo[i].set_comm_handles.remote(comm_handles) for i in range(N)])

# Run allreduce demo.
ray.get([demo[i].allreduce_demo.remote() for i in range(N)])
