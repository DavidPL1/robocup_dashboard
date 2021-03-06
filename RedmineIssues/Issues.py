# automatically generated by the FlatBuffers compiler, do not modify

# namespace: RedmineIssues

import flatbuffers

class Issues(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAsIssues(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = Issues()
        x.Init(buf, n + offset)
        return x

    # Issues
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # Issues
    def Issues(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from .Issue import Issue
            obj = Issue()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Issues
    def IssuesLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

def IssuesStart(builder): builder.StartObject(1)
def IssuesAddIssues(builder, issues): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(issues), 0)
def IssuesStartIssuesVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def IssuesEnd(builder): return builder.EndObject()
